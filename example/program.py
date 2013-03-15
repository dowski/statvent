"""Example program to demonstrate statvent usage."""
import os
import random
import time

import statvent


def main():
    pid = os.getpid()
    print "stats being recorded to /tmp/stats-pipe/%d.stats" % pid
    print "Try 'cat /tmp/stats-pipe/%d.stats'" % pid

    # Start the thread that will write out stats to the pipe.
    statvent.start_recorder()

    # Track a bunch of boring demo stats.
    i = 0
    while True:
        i += 1
        statvent.incr('foo.bar', 1)
        statvent.set('foo :: now', time.time())
        statvent.record('foo->baz->{0}', random.uniform(0.0, 5.0))
        if i % 50 == 0:
            print "tick ..."
        time.sleep(.1)

if __name__ == '__main__':
    main()
