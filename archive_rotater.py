#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A Wondrous Archive Rotation Script in Python 2.7
================================================

This script rotates files - typically backup archives. It offers three rotation algorithms - FIFO, Tower of Hanoi, and
tiered (a generalization of grandfather-father-son). It requires no configuration file, just command-line parameters.
The script is stand-alone (python 2.7 required) and tracks its state by applying a naming convention to rotated files.

See http://en.wikipedia.org/wiki/Backup_rotation_scheme

https://github.com/maxharp3r/archive-rotater


Use Case
--------

We assume that you have an archive, say `/path/to/foo/mydump.tgz` that is the result of an external process (e.g., `tar
-czf`, or `mysqldump`) that recurs (e.g., using `cron`). You will use this script to add this file into a rotation set.
If the size of the set is greater than the maximum number of files to keep (configurable), then the rotation set will
be trimmed according to a rotation algorithm, which is configurable.

Example of running:

    archive_rotater.py -v -n 5 /path/to/foo/mydump.tgz

This will rename mydump.tgz to something like this:

    /path/to/foo/mydump.tgz.2012-12-20-133640.backup-0

Given this configuration, the rotation script automatically keep at most 5 files in the rotation. When the script is run
six times, the set of archives would be too big, so the oldest will be deleted. This is an example of the simple (FIFO)
rotation algorithm.


Running
-------

See `hanoi_rotater.py -h` for documentation of command-line parameters.

To run doctests:

    python -m doctest -v archive_rotater.py


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

    archive_rotater.py --hanoi -v -n 6 /path/to/foo/mydump.tgz

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
    archive_rotater.py --tiered -v -n 6 -n 3 -n 12 /path/to/foo/mydump.tgz

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
    archive_rotater.py --tiered -v -n 6 /path/to/foo/mydump.tgz
    # hanoi with 4 slots:
    archive_rotater.py --tiered -v -n 1 -n 1 -n 1 -n 1 /path/to/foo/mydump.tgz


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
"""

import argparse
from datetime import datetime
from glob import iglob
import logging
import re
import os
import shutil
import sys

FILE_NAME_GLOB = '*.backup-*'
FILE_NAME_REGEX = r'backup-(?P<rotation_id>\d+)$'
FILE_NAME_TMPL = ".%(datetime_str)s.backup-%(rotation_id)d"
DATETIME_FORMAT = '%Y-%m-%d-%H%M%S'


class SimpleRotater(object):
    "FIFO implementation."

    def __init__(self, num_rotation_slots, verbose=False):
        self.num_rotation_slots = num_rotation_slots
        if verbose:
            logging.info("Rotation slots are: %s" % range(num_rotation_slots))

    def id_to_slot(self, rotation_id):
        """Tests:

        >>> r4 = SimpleRotater(4)
        >>> r4.id_to_slot(0)
        0
        >>> r4.id_to_slot(7)
        3
        """
        return rotation_id % self.num_rotation_slots


class HanoiRotater(object):
    "Tower of Hanoi implementation. A backup slot is a power of two (1, 2, 4, 8, ...)."

    def __init__(self, num_rotation_slots, verbose=False):
        self.num_rotation_slots = num_rotation_slots
        self.max_rotation_slot = 2 ** (num_rotation_slots - 1)

        if verbose:
            slots = [2 ** x for x in range(num_rotation_slots)]
            logging.info("Rotation slots are: %s" % slots)

    def id_to_slot(self, rotation_id):
        """Tests:

        >>> r3 = HanoiRotater(3)
        >>> r4 = HanoiRotater(4)
        >>> r5 = HanoiRotater(5)
        >>> r6 = HanoiRotater(6)

        The first backup (id 0) should be assigned the biggest slot available: 2^(n-1)
        >>> r3.id_to_slot(0)
        4
        >>> r4.id_to_slot(0)
        8
        >>> r5.id_to_slot(0)
        16

        >>> r4.id_to_slot(1)
        1
        >>> r4.id_to_slot(3)
        1
        >>> r4.id_to_slot(9)
        1
        >>> r4.id_to_slot(2)
        2
        >>> r4.id_to_slot(18)
        2
        >>> r4.id_to_slot(4)
        4
        >>> r4.id_to_slot(8)
        8
        >>> r4.id_to_slot(24)
        8

        >>> r5.id_to_slot(16)
        16
        >>> r5.id_to_slot(30)
        2
        >>> r5.id_to_slot(32)
        16
        >>> r6.id_to_slot(32)
        32
        """
        adjusted_rotation_id = rotation_id % self.max_rotation_slot
        if adjusted_rotation_id == 0:
            return self.max_rotation_slot

        # find the maximum power of two that divides cleanly into (rotation_id % max_rotation_slot)
        max_divisor = 1
        for divisor in (2 ** n for n in range(1, self.num_rotation_slots + 1)):
            if adjusted_rotation_id % divisor == 0:
                max_divisor = divisor
            else:
                break
        return max_divisor


class TieredRotater(object):
    "Tiered rotation schedule. This is a generalization of the grandfather-father-son rotation algorithm."

    def __init__(self, tier_sizes, verbose=False):
        self.num_tiers = len(tier_sizes)
        self.biggest_tier = self.num_tiers - 1
        self.tiers = []
        self.multipliers = []

        # given a list of tier sizes, configure a list of multipliers, and a list of tiers with slots
        multiplier = 1
        for tier_size in tier_sizes:
            slots = [(multiplier * n) - 1 for n in range(1, tier_size + 1)]
            self.tiers.append(slots)
            self.multipliers.append(multiplier)
            multiplier *= (1 + tier_size)
        if verbose:
            logging.info("Rotation slots are: %s" % self.tiers)
            logging.info("Multipliers are: %s" % self.multipliers)

    def id_to_slot(self, rotation_id):
        """Tests:

        >>> r0 = TieredRotater([2,2])
        >>> r0.id_to_slot(0)
        0
        >>> r0.id_to_slot(1)
        1
        >>> r0.id_to_slot(2)
        2
        >>> r0.id_to_slot(8)
        2
        >>> r0.id_to_slot(9)
        0

        >>> r1 = TieredRotater([4,3,2])
        >>> r1.id_to_slot(0)
        0
        >>> r1.id_to_slot(1)
        1
        >>> r1.id_to_slot(4)
        4
        >>> r1.id_to_slot(5)
        0
        >>> r1.id_to_slot(19)
        19
        >>> r1.id_to_slot(39)
        39

        >>> r1.id_to_slot(10)
        0
        >>> r1.id_to_slot(24)
        4
        >>> r1.id_to_slot(59)
        19
        """
        # try each tier, biggest multiple to smallest
        for i in reversed(range(self.num_tiers)):
            # divide the rotation_id by the multiplier .. if it is equal to the multiplier-1, then we've found our slot
            (quotient, remainder) = divmod(rotation_id, self.multipliers[i])
            if remainder == (self.multipliers[i] - 1):
                # wrap within a tier (based on how many slots in the tier) to prevent unlimited growth
                # the top tier is a special case - other tiers skip every nth run to promote to a higher tier
                modifier = len(self.tiers[i]) if (i == self.biggest_tier) else len(self.tiers[i]) + 1
                modified_quotient = quotient % modifier
                slot = modified_quotient * self.multipliers[i] + (self.multipliers[i] - 1)
                break
        return slot


def _rotated_files(path):
    "Generator. Yields the next rotated file as a tuple: (path, sequence)"
    for globbed_path in iglob(path + FILE_NAME_GLOB):
        match = re.search(FILE_NAME_REGEX, globbed_path)
        if match:
            yield globbed_path, int(match.group('rotation_id'))


def _most_recent_rotated_file_or_none(path):
    "Looks for hanoi_rotater generated files in the passed-in path, returns the maximum rotation_id found."
    rotated_files = [(path, rotation_id) for (path, rotation_id) in _rotated_files(path)]
    if not rotated_files:
        return None
    else:
        highest_rotated_file = max(rotated_files, key=lambda x: x[1])
        return highest_rotated_file[1]


def _locate_files_to_delete(rotater, path, rotation_id):
    "Looks for hanoi_rotater generated files that occupy the same slot that will be given to rotation_id."
    rotation_slot = rotater.id_to_slot(rotation_id)
    for a_path, a_rotation_id in [(p, n) for (p, n) in _rotated_files(path)]:
        if rotation_slot == rotater.id_to_slot(a_rotation_id):
            yield a_path


def main():
    # command line options
    parser = argparse.ArgumentParser(description='Move a file into a rotation of backup archives.')
    parser.add_argument('path', help='Path of input file to rotate')
    parser.add_argument('-n', '--num', dest='num_rotation_slots', type=int, action='append',
        help='Max number of files in the rotation')
    parser.add_argument('-v', '--verbose', dest='verbose', action="store_true", help='Print info messages to stdout')
    parser.add_argument('--ignore-missing', dest='ignore_missing', action="store_true",
        help='If the input file is missing, just log and exit normally, rather than exiting with an error')
    parser.add_argument('--simple', dest='simple_rotater', action="store_true",
        help='Use the first-in-first-out rotation pattern (default)')
    parser.add_argument('--hanoi', dest='hanoi_rotater', action="store_true",
        help='Use the Tower of Hanoi rotation pattern')
    parser.add_argument('--tiered', dest='tiered_rotater', action="store_true",
        help='Use the tiered rotation pattern')
    args = parser.parse_args()

    # logging
    log_level = logging.INFO if args.verbose else logging.WARN
    logging.basicConfig(stream=sys.stdout, level=log_level, format='%(message)s')

    # validate args
    if not args.num_rotation_slots:
        raise ValueError("Requires at least one rotation slot.")
    for n in args.num_rotation_slots:
        if n < 1:
            raise ValueError("Values less than one are not allowed for -n.")
    if len(args.num_rotation_slots) > 1 and not args.tiered_rotater:
        raise ValueError("Multiple -n values not allowed with the configured rotater.")
    if os.path.isdir(args.path):
        raise ValueError("The specified path (%s) is a directory, but must be a file." % (args.path))
    if not os.path.isfile(args.path):
        msg = "Specified file (%s) not found; exiting." % (args.path)
        if args.ignore_missing:
            logging.info(msg)
            sys.exit()
        else:
            raise IOError(msg)

    # build a rotater
    if args.hanoi_rotater:
        logging.info("Using Hanoi Rotater")
        rotater = HanoiRotater(args.num_rotation_slots[0], args.verbose)
    elif args.tiered_rotater:
        logging.info("Using Tiered Rotater")
        rotater = TieredRotater(args.num_rotation_slots, args.verbose)
    else:
        logging.info("Using Simple (FIFO) Rotater")
        rotater = SimpleRotater(args.num_rotation_slots[0], args.verbose)

    # find evidence of prior runs, reconstruct our rotation state from the file names
    dir, file_name = os.path.split(args.path)
    last_rotation_id = _most_recent_rotated_file_or_none(args.path)
    next_rotation_id = last_rotation_id + 1 if last_rotation_id is not None else 0
    to_delete = [p for p in _locate_files_to_delete(rotater, args.path, next_rotation_id)]
    if args.verbose:
        rotation_slot = rotater.id_to_slot(next_rotation_id)
        logging.info("New file: rotation_id=%s, rotation_slot=%s" % (next_rotation_id, rotation_slot))

    # rotate in the new file
    new_file_suffix = FILE_NAME_TMPL % \
        {'datetime_str': datetime.now().strftime(DATETIME_FORMAT), 'rotation_id': next_rotation_id}
    new_path = os.path.join(dir, file_name + new_file_suffix)
    shutil.move(args.path, new_path)
    logging.info("Moved %s to %s" % (args.path, new_path))

    # remove old files
    for f in to_delete:
        os.remove(f)
        logging.info("Removed %s" % (f))

    # log the set of rotated files
    if args.verbose:
        logging.info("Current rotation set:")
        for f, d in _rotated_files(args.path):
            a_rotation_slot = rotater.id_to_slot(d)
            logging.info("- %s / slot id %s" % (f, a_rotation_slot))


if (__name__ == '__main__'):
    main()
