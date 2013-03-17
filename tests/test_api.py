from collections import deque

import statvent
import statvent.stats


def test_incr_increments_the_given_stat_value():
    statvent.stats._stats['foo'] = 100
    statvent.incr('foo')
    assert statvent.stats._stats['foo'] == 101

def test_incr_by_a_value_increments_by_that_value():
    statvent.stats._stats['bar'] = 100
    statvent.incr('bar', 100)
    assert statvent.stats._stats['bar'] == 200

def test_set_sets_the_given_stat_value():
    assert 'baz' not in statvent.stats._stats
    statvent.set('baz', 3.14)
    assert statvent.stats._stats['baz'] == 3.14

def test_record_appends_values_to_a_deque():
    for i in range(3):
        statvent.record('this-n-that', i)
    assert statvent.stats._deques['this-n-that'] == deque([0,1,2])
