A Wondrous Archive Rotation Script in Python 2.7
================================================

This script rotates files - typically backup archives. It offers three rotation algorithms - FIFO, Tower of Hanoi, and
tiered (a generalization of grandfather-father-son). It requires no configuration file, just command-line parameters.
The script is stand-alone (python 2.7 required) and tracks its state by applying a naming convention to rotated files.

See http://en.wikipedia.org/wiki/Backup_rotation_scheme

https://github.com/maxharp3r/archive-rotator


Use Case
--------

We assume that you have an archive, say `/path/to/foo/mydump.tgz` that is the result of an external process (e.g., `tar
-czf`, or `mysqldump`) that recurs (e.g., using `cron`). You will use this script to add this file into a rotation set.
If the size of the set is greater than the maximum number of files to keep (configurable), then the rotation set will
be trimmed according to a rotation algorithm, which is configurable.

Example of running:

    archive_rotator.py -v -n 5 /path/to/foo/mydump.tgz

This will rename mydump.tgz to something like this:

    /path/to/foo/mydump.tgz.2012-12-20-133640.backup-0

Given this configuration, the rotation script automatically keep at most 5 files in the rotation. When the script is run
six times, the set of archives would be too big, so the oldest will be deleted. This is an example of the simple (FIFO)
rotation algorithm.


Running
-------

See `archive_rotator.py -h` for documentation of command-line parameters.

To run doctests:

    python -m doctest -v archive_rotator.py


Algorithms
==========

FIFO (simple)
-------------

This rotation scheme keeps the last n archives. It emphasizes recency at the cost of history and/or disk space.


Tower of Hanoi
--------------

This rotation scheme is described here: http://en.wikipedia.org/wiki/Backup_rotation_scheme#Tower_of_Hanoi
It emphasizes long history and saving disk space, but is not very tunable.

Example of running:

    archive_rotator.py --hanoi -v -n 6 /path/to/foo/mydump.tgz

Given this configuration, the rotation script automatically keep at most 6 files in the rotation, rotated every 1, 2, 4,
8, 16, and 32 runs, respectively. So, after 32 rotations, the directory will look something like this:

    /path/to/foo/mydump.tgz.2013-01-03-094732.backup-16
    /path/to/foo/mydump.tgz.2013-01-03-094734.backup-24
    /path/to/foo/mydump.tgz.2013-01-03-094735.backup-28
    /path/to/foo/mydump.tgz.2013-01-03-094736.backup-30
    /path/to/foo/mydump.tgz.2013-01-03-094737.backup-31
    /path/to/foo/mydump.tgz.2013-01-03-094738.backup-32


Tiered
------

This is a generalization of the grandfather-father-son rotation algorithm (described here -
http://en.wikipedia.org/wiki/Backup_rotation_scheme#Grandfather-father-son). This algorithm is capable of handling a
variety of rotation schedules.

This algorithm, unlike the others, accepts a list of one or more `-n` configurations. Each one is a "tier". For example:

    # three tiers: the first will hold 6 files, the second will hold 3, the third will hold 12
    archive_rotator.py --tiered -v -n 6 -n 3 -n 12 /path/to/foo/mydump.tgz

If the example above were run daily, we'd approximate 6 daily, 3 weekly, and 12 monthly backups in the rotation set.

You may configure any number of slots to each tier. If we have a single tier with 8 slots, the algorithm will behave
identically to the FIFO algorithm configured with eight slots. If we add a second tier with two slots, then the
algorithm will fill one of those two second-tier slots every ninth run. If we add a third tier with one slot, then the
algorithm will put the archive into the third tier slot for every two it puts into the second tier.

    Two tier example: -n 3 -n 2.
    id          : 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 ...
    maps to slot: 0 1 2 3 0 1 2 7 0 1  2  3  0  1  2 ...
    tier:       : 0 0 0 1 0 0 0 1 0 0  0  1  0  0  0 ...

    Three tier example: -n 2 -n 2 -n 2.
    id          : 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 ...
    maps to slot: 0 1 2 0 1 5 0 1 8 0  1  2  0  1  5 ...
    tier:       : 0 0 1 0 0 1 0 0 2 0  0  1  0  0  1 ...

    If we have tiers of size j, k, l, and m, then m is rotated every (j+1)(k+1)(l+1) runs.

This algorithm can replicate the behavior of both FIFO and Tower of Hanoi.

    # FIFO with 6 slots:
    archive_rotator.py --tiered -v -n 6 /path/to/foo/mydump.tgz
    # hanoi with 4 slots:
    archive_rotator.py --tiered -v -n 1 -n 1 -n 1 -n 1 /path/to/foo/mydump.tgz


MIT License
-----------

Copyright (c) 2012 Max Harper

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

