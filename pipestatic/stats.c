#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <pthread.h>
#include <string.h>
#include <assert.h>

#include "stats.h"

#define STAT_MAX 64
#define STAT_OUTPUT_BYTES 8192

static int n_stats = 0;
static pipestat *all_stats[STAT_MAX];

void
stat_incr(pipestat *stat)
{
    switch(stat->type) {
        case STAT_TYPE_DOUBLE :
           stat->value.double_value++;
           break;
        case STAT_TYPE_LONG :
           stat->value.long_value++;
           break;
    }
}

void
stat_incrv_d(pipestat *stat, double v)
{
    assert(stat->type == STAT_TYPE_DOUBLE);
    stat->value.double_value += v;
}

void
stat_incrv_l(pipestat *stat, long v)
{
    assert(stat->type == STAT_TYPE_LONG);
    stat->value.long_value += v;
}

void
stat_set_d(pipestat *stat, double v)
{
    assert(stat->type == STAT_TYPE_DOUBLE);
    stat->value.double_value = v;
}

void
stat_set_l(pipestat *stat, long v)
{
    assert(stat->type == STAT_TYPE_LONG);
    stat->value.long_value = v;
}

pipestat *
init_stat(char *name, stat_type t)
{
    pipestat *ps;
    if (!(ps = malloc(sizeof(pipestat)))) {
        return NULL;
    }
    strncpy(&(ps->name[0]), name, 256);
    ps->type = t;
    switch (t) {
        case STAT_TYPE_LONG :
            ps->value.long_value = 0;
            break;
        case STAT_TYPE_DOUBLE :
            ps->value.double_value = 0.0;
            break;
    }
    all_stats[n_stats++] = ps;
    return ps;
}

void *stats_loop(void *unused)
{
    char pipe_path[128], out_data[STAT_OUTPUT_BYTES];
    int fd, out_len, i;
    struct stat dir_stat;
    pipestat current_stat;

    if (stat("/tmp/stats-pipe", &dir_stat)) {
        perror("could not stat named pipe directory, not logging stats");
        return 0;
    }
    if (!S_ISDIR(dir_stat.st_mode)) {
        fprintf(stderr, "named pipe path is not a directory, not logging stats\n");
        return 0;
    }

    snprintf(pipe_path, 128, "/tmp/stats-pipe/%d.stats", getpid());

    /* we don't need to worry about cleaning up pipes if we're
     * killed, because pipestatic will do so for us */
    while (1) {
        out_len = 0;
        if (mkfifo(pipe_path, 0644)) {
            perror("stats mkfifo");
            if (errno == EACCES) {
                fprintf(stderr, "not logging stats\n");
                return 0;
            }
        }

        if ((fd = open(pipe_path, O_WRONLY)) == -1) {
            perror("stats open");
        }

        for (i=0;i<n_stats;++i) {
            current_stat = *(all_stats[i]);
            out_len += snprintf(&out_data[out_len], STAT_OUTPUT_BYTES, "%s: ", current_stat.name);
            switch (current_stat.type) {
                case STAT_TYPE_LONG :
                    out_len += snprintf(&out_data[out_len], STAT_OUTPUT_BYTES, "%ld\n", current_stat.value.long_value);
                    break;
                case STAT_TYPE_DOUBLE :
                    out_len += snprintf(&out_data[out_len], STAT_OUTPUT_BYTES, "%f\n", current_stat.value.double_value);
                    break;
                default :
                    fprintf(stderr, "unknown stat type: %d", (int)(current_stat.type));
                    break;
            }
        }

        if (write(fd, out_data, out_len) == -1) {
            perror("stats write");
        }

        if (close(fd)) {
            perror("stats close");
        }

        if (unlink(pipe_path)) {
            perror("stats unlink");
        }
    }
}

void
init_stats()
{
    pthread_t stats_thread = {0};
    pthread_create(&stats_thread, NULL, stats_loop, NULL);
}
