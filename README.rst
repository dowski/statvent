statvent
==========

statvent gives you three things:

1. A developer API for recording metrics in your library or application.
2. A deployer API that writes stats to a named pipe.
3. A simple web service that will read from *all* named pipes on a host and
   serve the results as JSON.

The Developer API
=================

It's really simple. There are three functions for recording data.

``statvent.incr(name, value=1)``

    Call it with the ``name`` of a stat and it will increment it. If it doesn't
    exist yet, it will initialize it to the given ``value`` (defaults to
    ``1``).

    It's very useful for keeping tabs on events that happen within your apps.

``statvent.set(name, value)``

    Call it with the ``name`` of a stat and a value. The stat will be set to
    that value.

    This function is useful for values that can fluctuate, like number of
    concurrent users, connections to a database, winning streaks, etc.

``statvent.record(name, value, format_func=str.format)``

    Call it with the ``name`` of a stat and a value. By default the ``name``
    must include a ``{0}`` format placeholder. Internally, the value is
    appended to a deque. When the pipe is read, the stats recorder will
    calculate some aggregate statistics from the contents of the deque
    (by default a few percentile breaks and the mean).
    
    **If your stat name scheme conflicts with the default ``str.format``
    function you can provide your own function to format the stat name to
    include the calculated percentile labels.**

The names of stats just need to be byte strings. You can format them however
you want, include whatever punctuation makes you happy, etc. If you want
percentiles or other calculated stats (using ``statvent.record``), you'll need
to take a bit of extra care when formatting your stat names.

Values can be integers or floats. Be aware that once you use a float, that stat
will remain a float. It probably doesn't matter that much, but now you know.

The Deployer API
================

Notice that there is no mention of an API for reading stats. That's because the
creation and consumption of your application's metrics should be decoupled. The
decoupling is accomplished by writing the data out to a named pipe.

``statvent.start_recorder()``

    Starts a thread that writes the application stats to a named pipe.

    The thread blocks on the open system call won't spend any of your
    application's resources until another process opens the pipe for reading.

The Named Pipe
--------------

By default the pipes are located in ``/tmp/stats-pipe/`` and are named
``<pid>.stats`` where ``<pid>`` is the UNIX process ID that is writing data
into that named pipe. You can change the location where pipes are
written/read by setting the ``statvent.stats.config['pipe_dir']`` path. Make
sure your processes have permission to write there though.

Each stat is written to its own line in the named pipe. The name of the
stat and the current value are separated by a colon `:` followed by a
space. The value follows and is either a floating point value or an integer
value. Then there is a newline character. Here's an example::

    a.b.c.d: 42
    My Nice Stat: 123.45
    another[one]: 0

You can peek at the current state of your app by running ``cat`` against the
named pipe, or have a process that does that regularly and inserts the results
into a database to track the data over time.

The Web Service
===============

If you don't want to mess with consuming a weird plain-text format like you get
from the named pipe, and you want to collect stats from more than one process
on a host, the JSON web service might interest you.

It will sum the values of all stats and serve them up as JSON. Try running
``python -m statvent.web`` as a script to see it in action. 
