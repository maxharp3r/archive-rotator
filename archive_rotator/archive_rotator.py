#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Archive Rotator's only module.
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
FILE_NAME_REGEX = r'backup-(?P<rotation_id>\d+)'
FILE_NAME_TMPL = ".%(datetime_str)s.backup-%(rotation_id)d%(ext)s"
DATETIME_FORMAT = '%Y-%m-%d-%H%M%S'


class SimpleRotator(object):
    """FIFO implementation."""

    def __init__(self, num_rotation_slots, verbose=False):
        self.num_rotation_slots = num_rotation_slots
        if verbose:
            logging.info("Rotation slots are: %s" % range(num_rotation_slots))

    def id_to_slot(self, rotation_id):
        return rotation_id % self.num_rotation_slots


class HanoiRotator(object):
    """Tower of Hanoi implementation. A backup slot is a power of two (1, 2, 4, 8, ...)."""

    def __init__(self, num_rotation_slots, verbose=False):
        self.num_rotation_slots = num_rotation_slots
        self.max_rotation_slot = 2 ** (num_rotation_slots - 1)

        if verbose:
            slots = [2 ** x for x in range(num_rotation_slots)]
            logging.info("Rotation slots are: %s" % slots)

    def id_to_slot(self, rotation_id):
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


class TieredRotator(object):
    """Tiered rotation schedule. This is a generalization of the grandfather-father-son rotation algorithm."""

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
        slot = 0
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
    """Generator. Yields the next rotated file as a tuple: (path, sequence)"""
    for globbed_path in iglob(path + FILE_NAME_GLOB):
        match = re.search(FILE_NAME_REGEX, globbed_path)
        if match:
            yield globbed_path, int(match.group('rotation_id'))


def _most_recent_rotated_file_or_none(path):
    """Looks for hanoi_rotator generated files in the passed-in path, returns the maximum rotation_id found."""
    rotated_files = [(path, rotation_id) for (path, rotation_id) in _rotated_files(path)]
    if not rotated_files:
        return None
    else:
        highest_rotated_file = max(rotated_files, key=lambda x: x[1])
        return highest_rotated_file[1]


def _locate_files_to_delete(rotator, path, rotation_id):
    """Looks for hanoi_rotator generated files that occupy the same slot that will be given to rotation_id."""
    rotation_slot = rotator.id_to_slot(rotation_id)
    for a_path, a_rotation_id in [(p, n) for (p, n) in _rotated_files(path)]:
        if rotation_slot == rotator.id_to_slot(a_rotation_id):
            yield a_path


def main():
    # command line options
    parser = argparse.ArgumentParser(description='Move a file into a rotation of backup archives.')
    parser.add_argument('path', help='Path of input file to rotate')
    parser.add_argument('-n', '--num', dest='num_rotation_slots', type=int, action='append',
                        help='Max number of files in the rotation')
    parser.add_argument('-v', '--verbose', dest='verbose', action="store_true", help='Print info messages to stdout')
    parser.add_argument('--ext', dest='ext', default='', help='Look for and preserve the named file extension')
    parser.add_argument('--ignore-missing', dest='ignore_missing', action="store_true",
                        help='If the input file is missing, log and exit normally rather than exiting with an error')
    parser.add_argument('--simple', dest='simple_rotator', action="store_true",
                        help='Use the first-in-first-out rotation pattern (default)')
    parser.add_argument('--hanoi', dest='hanoi_rotator', action="store_true",
                        help='Use the Tower of Hanoi rotation pattern')
    parser.add_argument('--tiered', dest='tiered_rotator', action="store_true",
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
    if len(args.num_rotation_slots) > 1 and not args.tiered_rotator:
        raise ValueError("Multiple -n values not allowed with the configured rotator.")
    if os.path.isdir(args.path):
        raise ValueError("The specified path (%s) is a directory, but must be a file." % args.path)
    if not os.path.isfile(args.path):
        msg = "Specified file (%s) not found; exiting." % args.path
        if args.ignore_missing:
            logging.info(msg)
            sys.exit()
        else:
            raise IOError(msg)
    if args.ext and args.ext[0] != ".":
        raise ValueError("File extension (--ext) must start with the . character.")
    if args.ext and not args.path.endswith(args.ext):
        raise ValueError("The file %s does not have the file extension %s" % (args.path, args.ext))

    # build a rotator
    if args.hanoi_rotator:
        logging.info("Using Hanoi Rotator")
        rotator = HanoiRotator(args.num_rotation_slots[0], args.verbose)
    elif args.tiered_rotator:
        logging.info("Using Tiered Rotator")
        rotator = TieredRotator(args.num_rotation_slots, args.verbose)
    else:
        logging.info("Using Simple (FIFO) Rotator")
        rotator = SimpleRotator(args.num_rotation_slots[0], args.verbose)

    # if a file extension was specified, trim it off the path
    modified_path = args.path if not args.ext else args.path.rsplit(args.ext, 1)[0]

    # find evidence of prior runs, reconstruct our rotation state from the file names
    dir_name, file_name = os.path.split(modified_path)
    last_rotation_id = _most_recent_rotated_file_or_none(modified_path)
    next_rotation_id = last_rotation_id + 1 if last_rotation_id is not None else 0
    to_delete = [p for p in _locate_files_to_delete(rotator, modified_path, next_rotation_id)]
    if args.verbose:
        rotation_slot = rotator.id_to_slot(next_rotation_id)
        logging.info("New file: rotation_id=%s, rotation_slot=%s" % (next_rotation_id, rotation_slot))

    # rotate in the new file
    new_file_suffix = FILE_NAME_TMPL % \
        {'datetime_str': datetime.now().strftime(DATETIME_FORMAT), 'rotation_id': next_rotation_id, 'ext': args.ext}
    new_path = os.path.join(dir_name, file_name + new_file_suffix)
    shutil.move(args.path, new_path)
    logging.info("Moved %s to %s" % (args.path, new_path))

    # remove old files
    for f in to_delete:
        os.remove(f)
        logging.info("Removed %s" % f)

    # log the set of rotated files
    if args.verbose:
        logging.info("Current rotation set:")
        for f, d in _rotated_files(modified_path):
            a_rotation_slot = rotator.id_to_slot(d)
            logging.info("- %s / slot id %s" % (f, a_rotation_slot))


if __name__ == '__main__':
    main()
