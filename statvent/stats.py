"""An API for recording stats about your Python application.

The goal of this library is to make it as simple as possible to record stats
about your running application.

The stats are written to a named pipe. By default, the named pipes are stored
in /tmp/stats-pipe. They are named "<PID>.stats". Integer and floating point
values are supported.

The API is simple. You can `incr` or `set` values. Use the standard `cat`
command or whichever tool you prefer to read out the data.

"""
import atexit
import os
import threading
import math

from collections import defaultdict, deque


# Developer API
# =============

def set(name, value):
    """Set the given stat name to value.

    """
    _stats[name] = value

def incr(name, value=1):
    """Increment the given stat name by value.

    """
    _stats[name] += value

def record(name, value, format_func=str.format):
    """Record an instance of the value for the given stat name.

    The `name` must have a "{0}" replacement token in it so aggregate
    calculations have a chance to label the aggregate value.

    """
    _deques[name].append(value)
    if name not in _formatters:
        _formatters[name] = format_func

def get_all():
    """Return a dictionary of the recorded stats."""
    return dict(_stats)


# Deployer API
# ============

config = {
    'pipe_dir': '/tmp/stats-pipe',
}

def start_recorder():
    """Starts a dedicated thread for handling the stats named pipe.

    Ensures that only a single instance of the thread starts. Creates the
    directory for holding the named pipes, if needed.

    """
    global _recorder

    try:
        os.mkdir(config['pipe_dir'])
    except OSError, e:
        if e.errno == 17:
            # Directory already exists.
            pass
        else:
            raise

    if not _recorder:
        _recorder = _StatRecorder()
        _recorder.setDaemon(True)
        _recorder.start()


# Private Code
# ============

_stats = defaultdict(int)
_deques = defaultdict(lambda: deque(list(), 100))
_recorder = None
_formatters = {}


def basic_percentiles(name, vals):
    n_vals = len(vals)
    format_func = _formatters[name]
    PERCENTILES = [(50, "median"), (95, "95th"), (99, "99th"), (100, "100th")]

    for n,label in PERCENTILES:
        index = int(math.floor(n_vals * (n * 0.01))) - 1
        if index < 0:
            index = 0
        yield (format_func(name, label), vals[index] if vals else 0.0)
    if n_vals:
        yield (format_func(name, "mean"), sum(vals) / n_vals)


class _StatRecorder(threading.Thread):
    def __init__(self, calculator=basic_percentiles, deque_size=100):
        super(_StatRecorder, self).__init__()
        default_filename = "%s.stats" % (os.getpid())
        self.statpath = os.path.join(config['pipe_dir'], default_filename)
        self.calculator = calculator

        _deques.default_factory = (lambda: deque(list(), deque_size))

    def set_deques(self):
        # Does aggregate calculations on the values recorded in _deques and
        # calls our `set` function to get them in the _stats dictionary for
        # pipe output.
        for name, vals in _deques.iteritems():
            vals = sorted(vals)
            for (metric, val) in self.calculator(name, vals):
                # NOTE This call is *not* the builtin set type; its our own
                # little API set function. An unfortunate collision that we run
                # into on our way to a nice statvent API.
                set(metric, val)

    def run(self):
        # Try and cleanup the named pipe after we exit. Not guaranteed to be
        # called (in the case of a SIGKILL or machine crash or ...).
        @atexit.register
        def cleanup():
            try:
                os.unlink(self.statpath)
            except OSError:
                pass

        while True:
            os.mkfifo(self.statpath)

            # NOTE: The thread blocks here until a proc opens the pipe to read.
            f = open(self.statpath, 'w')

            self.set_deques()
            for name, value in get_all().iteritems():
                if isinstance(value, float):
                    f.write('%s: %f\n' % (name, value))
                elif isinstance(value, (int, long)):
                    f.write('%s: %d\n' % (name, value))
            f.close()
            os.unlink(self.statpath)

