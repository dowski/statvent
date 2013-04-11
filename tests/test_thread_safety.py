import threading
import Queue

import statvent


jobs = Queue.Queue()
done = Queue.Queue()

def do_inc():
    while True:
        job = jobs.get()
        if job is None:
            done.put(None)
            break
        statvent.incr('thread.test')

def test_10k_iterations_in_N_threads_results_in_10k_incrs():
    n = 25
    threads = []
    for i in xrange(n):
        t = threading.Thread(target=do_inc)
        t.start()
        threads.append(t)
    for i in xrange(5000):
        jobs.put(i)
    for i in xrange(n):
        jobs.put(None)
    for i in xrange(n):
        done.get()

    actual = statvent.get_all()['thread.test']
    assert actual == 5000, actual



