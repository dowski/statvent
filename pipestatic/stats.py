"""An API for recording stats about your Python application.

The goal of this module is to make it as simple as possible to record stats
about your running application.

The stats are written to a named pipe. By default, the named pipes are stored
in /tmp/stats-pipe. They are named "<PID>.stats". Integer and floating point
values are supported.

The API is simple. You can `incr` or `set` values. Use the standard `cat`
command or whichever tool you prefer to read out the data.

You can also run this module as a command and it will read the data from your
stat pipes and serve it up as JSON via HTTP. It tries to gracefully handle
dead pipes, and will unlink them if it finds any.

Don't use this library for recording values that required many degrees of
precision.  Some precision is lost when the values are read from the named
pipe.

"""
import atexit
import optparse
import os
import signal
import threading
import time
import traceback
import urlparse

import simplejson

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict


INTERRUPTED_SYSTEM_CALL = 4
PIPE_OPEN_TIMEOUT = 0.1

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


def http_stat_publisher(ip='', port=7828, path='/stats'):
    class _StatsHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse.urlparse(self.path)
            self.headers['Content-Type'] = 'application/json'

            if parsed.path == path:
                collected_stats = _load_all_from_pipes()
                status_code = 200
                body = simplejson.dumps({
                    'stats':collected_stats,
                    'timestamp':time.time(),
                })
            else:
                status_code = 400
                body = simplejson.dumps({
                    'message':'The requested resource was not found',
                    'path':parsed.path,
                })
            self.send_response(status_code)
            self.end_headers()
            self.wfile.write(body)
    HTTPServer((ip, port), _StatsHandler).serve_forever()

# Private Code
# ============

_stats = defaultdict(int)
_recorder = None

class _StatRecorder(threading.Thread):

    def __init__(self):
        super(_StatRecorder, self).__init__()
        default_filename = "%s.stats" % (os.getpid())
        self.statpath = os.path.join(config['pipe_dir'], default_filename)

    def run(self):

        @atexit.register
        def cleanup():
            try:
                os.unlink(self.statpath)
            except OSError:
                pass

        while True:
            os.mkfifo(self.statpath)
            f = open(self.statpath, 'w')
            for name, value in get_all().iteritems():
                if isinstance(value, float):
                    f.write('%s: %f\n' % (name, value))
                elif isinstance(value, (int, long)):
                    f.write('%s: %d\n' % (name, value))
            f.close()
            os.unlink(self.statpath)

# FIXME The function below is begging to be refactored.
def _load_all_from_pipes():
    all_stats = defaultdict(int)
    if os.path.exists(config['pipe_dir']):
        for filename in os.listdir(config['pipe_dir']):
            pipe_path = os.path.join(config['pipe_dir'], filename)
            _set_pipe_open_timeout(PIPE_OPEN_TIMEOUT)
            try:
                with open(pipe_path) as pipe:
                    _clear_pipe_open_timeout()
                    for line in pipe:
                        cleaned = line.strip()
                        name, raw_value = cleaned.rsplit(':', 1)
                        try:
                            value = int(raw_value.strip())
                        except ValueError:
                            value = float(raw_value.strip())
                        all_stats[name.strip()] += value
            except IOError, e:
                if e.errno == INTERRUPTED_SYSTEM_CALL:
                    # Our timeout fired - no one is writing to this pipe.
                    # Let's try and clean it up.
                    try:
                        os.unlink(pipe_path)
                    except:
                        traceback.print_exc()
                else:
                    raise
    return dict(all_stats)

def _set_pipe_open_timeout(timeout):
    interval = 0

    signal.setitimer(signal.ITIMER_REAL, timeout, interval)

    if timeout:
        def _noop(sig, frame):
            # Don't do anything with the signal - just pass on.
            pass
        signal.signal(signal.SIGALRM, _noop)
    else:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)


def _clear_pipe_open_timeout():
    _set_pipe_open_timeout(0)

def main():
    parser = optparse.OptionParser()

    parser.add_option(
        '-p', '--port', type="int", help="The port to listen on.", default=7828,
    )
    parser.add_option(
        '-i', '--ip',  help="The IP address to listen on.", default='',
    )
    parser.add_option(
        '-l', '--path',  help="The HTTP path for serving stats.",
        default="/stats",
    )
    parser.add_option(
        '-d', '--pipe-dir', help="The directory where the stats pipes live.",
    )
    opts, args = parser.parse_args()
    if opts.pipe_dir:
        config['pipe_dir'] = opts.pipe_dir
    http_stat_publisher(opts.ip, opts.port, opts.path)

if __name__ == '__main__':
    main()
