Archive Rotator
===============

.. image:: https://img.shields.io/pypi/v/archive-rotator.svg
        :target: https://pypi.python.org/pypi/archive-rotator

.. image:: https://img.shields.io/travis/maxharp3r/archive-rotator.svg
        :target: https://travis-ci.org/maxharp3r/archive-rotator

.. image:: https://readthedocs.org/projects/archive-rotator/badge/?version=latest
        :target: https://readthedocs.org/projects/archive-rotator/?badge=latest
        :alt: Documentation Status

Flexible utility for rotating backup files.

* Free software: MIT license
* Documentation: https://archive-rotator.readthedocs.org.
* Code: https://github.com/maxharp3r/archive-rotator

This utility rotates files - typically backup archives. It offers three rotation algorithms - FIFO, Tower of Hanoi, and
tiered (a generalization of grandfather-father-son). It requires no configuration file, just command-line parameters.
The script is stand-alone (python required) and tracks its state by applying a naming convention to rotated files.

Learn about the concept of archive rotation: http://en.wikipedia.org/wiki/Backup_rotation_scheme


Example Use
-----------

We assume that you have an archive, say `/path/to/foo/mydump.tgz` that is the result of an external process (e.g., `tar
-czf`, or `mysqldump`) that recurs (e.g., using `cron`). You will use this script to add this file into a rotation set.
If the size of the set is greater than the maximum number of files to keep (configurable), then the rotation set will
be trimmed according to a rotation algorithm, which is configurable.

Example of running::

    archive-rotator -v -n 5 /path/to/foo/mydump.tgz

This will rename mydump.tgz to something like this::

    /path/to/foo/mydump.tgz.2012-12-20-133640.backup-0

Given this configuration, the rotation script automatically keep at most 5 files in the rotation. When the script is run
six times, the set of archives would be too big, so the oldest will be deleted. This is an example of the simple (FIFO)
rotation algorithm.
