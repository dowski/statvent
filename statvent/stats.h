#include <stdio.h>

typedef enum stat_type {STAT_TYPE_DOUBLE, STAT_TYPE_LONG} stat_type;

typedef struct pipestat {
    stat_type type;
    char name[256];
    union {
        double double_value;
        long long_value;
    } value;
} pipestat;

#define STAT_INCRV(stat, v) stat->type == STAT_TYPE_DOUBLE ? stat_incrv_d(stat, v) : stat_incrv_l(stat, v)
#define STAT_SET(stat, v) stat->type == STAT_TYPE_DOUBLE ? stat_set_d(stat, v) : stat_set_l(stat, v)

void init_stats(void);
pipestat *init_stat(char *name, stat_type t);

void incr_stat(pipestat *stat);
void stat_incrv_d(pipestat *stat, double v);
void stat_incrv_l(pipestat *stat, long v);
void stat_set_d(pipestat *stat, double v);
void stat_set_l(pipestat *stat, long v);
