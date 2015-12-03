#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
archive_rotator.cli
-------------------

Handles command line arguments.

Example::

    archive-rotator -v -n 5 /path/to/foo/mydump.tgz

"""

import argparse
import logging
import os
import sys

from archive_rotator import rotator
from archive_rotator.algorithms import \
    SimpleRotator, HanoiRotator, TieredRotator


def main():
    parser = argparse.ArgumentParser(
        description='Move a file into a rotation of backup archives.')
    parser.add_argument('path', help='Path of input file to rotate')
    parser.add_argument('-n', '--num', dest='num_rotation_slots', type=int,
                        action='append',
                        help='Max number of files in the rotation')
    parser.add_argument('-v', '--verbose', dest='verbose', action="store_true",
                        help='Print info messages to stdout')
    parser.add_argument('--ext', dest='ext', default='',
                        help='Look for and preserve the named file extension')
    parser.add_argument('--destination-dir', dest='destination_dir',
                        help='Put the rotated archive in this directory.'
                             'Use if the rotated archives live in a '
                             'different directory from the source file.')
    parser.add_argument('--ignore-missing', dest='ignore_missing',
                        action="store_true",
                        help='If the input file is missing, log and exit '
                             'normally rather than exiting with an error')
    parser.add_argument('--simple', dest='simple_rotator', action="store_true",
                        help='Use the first-in-first-out rotation pattern '
                             '(default)')
    parser.add_argument('--hanoi', dest='hanoi_rotator', action="store_true",
                        help='Use the Tower of Hanoi rotation pattern')
    parser.add_argument('--tiered', dest='tiered_rotator', action="store_true",
                        help='Use the tiered rotation pattern')
    args = parser.parse_args()

    # logging
    log_level = logging.INFO if args.verbose else logging.WARN
    logging.basicConfig(stream=sys.stdout, level=log_level,
                        format='%(message)s')

    # validate args
    if not args.num_rotation_slots:
        raise ValueError("Requires at least one rotation slot.")
    for n in args.num_rotation_slots:
        if n < 1:
            raise ValueError("Values less than one are not allowed for -n.")
    if len(args.num_rotation_slots) > 1 and not args.tiered_rotator:
        raise ValueError(
            "Multiple -n values not allowed with the configured rotator.")
    if os.path.isdir(args.path):
        raise ValueError("The specified path (%s) is a directory, but must be "
                         "a file." % args.path)

    # validate path
    if not os.path.isfile(args.path):
        msg = "Specified file (%s) not found; exiting." % args.path
        if args.ignore_missing:
            logging.info(msg)
            sys.exit()
        else:
            raise IOError(msg)

    # validate ext
    if args.ext and args.ext[0] != ".":
        raise ValueError(
            "File extension (--ext) must start with the . character.")
    if args.ext and not args.path.endswith(args.ext):
        raise ValueError("The file %s does not have the file extension %s"
                         % (args.path, args.ext))

    # validate destination_dir
    if args.destination_dir and not os.path.isdir(args.destination_dir):
        raise ValueError("The specified destination directory "
                         "(--destination-dir) is not found or is not a "
                         "directory.")

    # build a rotator
    if args.hanoi_rotator:
        logging.info("Using Hanoi Rotator")
        algorithm = HanoiRotator(args.num_rotation_slots[0], args.verbose)
    elif args.tiered_rotator:
        logging.info("Using Tiered Rotator")
        algorithm = TieredRotator(args.num_rotation_slots, args.verbose)
    else:
        logging.info("Using Simple (FIFO) Rotator")
        algorithm = SimpleRotator(args.num_rotation_slots[0], args.verbose)

    # go!
    paths = rotator.Paths(args.path, args.ext, args.destination_dir)
    rotator.rotate(algorithm, paths, args.verbose)


if __name__ == '__main__':
    main()
