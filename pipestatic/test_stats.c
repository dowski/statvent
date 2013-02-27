#include "stats.h"


int
main(int argc, char **argv)
{
    init_stats();

    int i;
    pipestat *ticks = init_stat("my.ticks", STAT_TYPE_DOUBLE);
    pipestat *tocks = init_stat("my.tocks", STAT_TYPE_LONG);

    stat_incr(ticks);
    for (i=0;i<10;++i) {
        STAT_INCRV(tocks, 2);
        stat_incrv_d(ticks, 1.5);
    }
    stat_incr(tocks);
    while (1) {
        sleep(1);
        stat_incr(ticks);
    }
    return 0;
}

