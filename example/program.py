"""Example program to demonstrate statvent usage."""
import os
import random
import time

from statvent import stats


def main():
    pid = os.getpid()
    print "stats being recorded to /tmp/stats-pipe/%d.stats" % pid
    print "Try 'cat /tmp/stats-pipe/%d.stats'" % pid
    stats.start_recorder()
    i = 0
    while True:
        i += 1
        stats.incr('foo.bar', 1)
        stats.set('foo :: now', time.time())
        stats.record('foo->baz->{0}', random.uniform(0.0, 5.0))
        if i % 50 == 0:
            print "tick ..."
        time.sleep(.1)
if __name__ == '__main__':
    main()
