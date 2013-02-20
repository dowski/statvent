#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <pthread.h>

typedef enum stat_type {STAT_TYPE_DOUBLE, STAT_TYPE_LONG} stat_type;
typedef struct pipestat {
    stat_type type;
    const char *name;
    union {
        double double_value;
        long long_value;
    } value;
} pipestat;

#define STAT_MAX 64
#define STAT_OUTPUT_BYTES 8192
#define STAT_INCR(stat) stat->type == STAT_TYPE_DOUBLE ? stat->value.double_value++ : stat->value.long_value++
#define STAT_INCRV(stat, v) stat->type == STAT_TYPE_DOUBLE ? (stat->value.double_value += (v)) : (stat->value.long_value += (v))
#define STAT_SET(stat, v) stat->type == STAT_TYPE_DOUBLE ? stat->value.double_value = v : stat->value.long_value = v
#define STAT_PRINT(stat) stat->type == STAT_TYPE_DOUBLE ? printf("%s: %f\n", stat->name, stat->value.double_value) : printf("%s: %ld\n", stat->name, stat->value.long_value)

static int n_stats = 0;
static pipestat *all_stats[STAT_MAX];

pipestat *
init_stat(const char *name, stat_type t)
{
    pipestat *ps;
    if (!(ps = malloc(sizeof(pipestat)))) {
        return NULL;
    }
    ps->name = name;
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

int
main(int argc, char **argv)
{
    int i;
    pthread_t stats_thread = {0};

    pthread_create(&stats_thread, NULL, stats_loop, NULL);
    pipestat *ticks = init_stat("my.ticks", STAT_TYPE_DOUBLE);
    pipestat *tocks = init_stat("my.tocks", STAT_TYPE_LONG);

    STAT_INCR(ticks);
    for (i=0;i<10;++i) {
        STAT_INCRV(tocks, 2);
    }
    STAT_INCR(tocks);
    STAT_PRINT(ticks);
    STAT_PRINT(tocks);
    while (1) {
        sleep(1);
        STAT_INCR(ticks);
    }
    return 0;
}

