#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
archive_rotator.rotator
-----------------------

File moving logic goes here.
"""

from datetime import datetime
from glob import iglob
import logging
import re
import os
import shutil

FILE_NAME_GLOB = '*.backup-*'
FILE_NAME_REGEX = r'backup-(?P<rotation_id>\d+)'
FILE_NAME_TMPL = ".%(datetime_str)s.backup-%(rotation_id)d%(ext)s"
DATETIME_FORMAT = '%Y-%m-%d-%H%M%S'


class Paths(object):
    """
    Holds configuration of paths. Computes the output path.
    """

    @property
    def full_input_path(self):
        return os.path.join(self.input_dir, self.input_fn + self.input_ext)

    @property
    def output_path_no_ext(self):
        return os.path.join(self.output_dir, self.input_fn)

    @staticmethod
    def _get_now():
        # XXX: this is here to facilitate mocking in unit tests
        return datetime.now()

    def full_output_path(self, next_rotation_id):
        suffix = \
            FILE_NAME_TMPL % \
            {'datetime_str': self._get_now().strftime(DATETIME_FORMAT),
             'rotation_id': next_rotation_id,
             'ext': self.input_ext}
        return os.path.join(self.output_dir, self.input_fn + suffix)

    def __init__(self, path, ext, destination_dir):
        # if a file extension was specified, trim it off the path
        # we do not try to guess extensions, only use if explicitly configured
        path_without_ext = path if not ext else path.rsplit(ext, 1)[0]

        dir_name, file_name = os.path.split(path_without_ext)

        self.input_dir = dir_name
        self.input_fn = file_name
        self.input_ext = ext if ext else ""
        self.output_dir = destination_dir if destination_dir else dir_name


def _rotated_files(path):
    """Generator. Yields the next rotated file as a tuple:
    (path, rotation_id)
    """
    for globbed_path in iglob(path + FILE_NAME_GLOB):
        match = re.search(FILE_NAME_REGEX, globbed_path)
        if match:
            yield globbed_path, int(match.group('rotation_id'))


def _next_rotation_id(rotated_files):
    """Given the hanoi_rotator generated files in the output directory,
    returns the rotation_id that will be given to the current file. If there
    are no existing rotated files, return 0.
    """
    if not rotated_files:
        return 0
    else:
        highest_rotated_file = max(rotated_files, key=lambda x: x[1])
        return highest_rotated_file[1] + 1


def _locate_files_to_delete(algorithm, rotated_files, next_rotation_id):
    """Looks for hanoi_rotator generated files that occupy the same slot
    that will be given to rotation_id.
    """
    rotation_slot = algorithm.id_to_slot(next_rotation_id)
    for a_path, a_rotation_id in rotated_files:
        if rotation_slot == algorithm.id_to_slot(a_rotation_id):
            yield a_path


def _move_files(algorithm, paths, verbose):
    # reconstruct rotation state from the file names in output dir
    rotated_files = list(_rotated_files(paths.output_path_no_ext))
    next_rotation_id = _next_rotation_id(rotated_files)
    to_delete = list(_locate_files_to_delete(algorithm,
                                             rotated_files,
                                             next_rotation_id))
    if verbose:
        rotation_slot = algorithm.id_to_slot(next_rotation_id)
        logging.info("New file: rotation_id=%s, rotation_slot=%s"
                     % (next_rotation_id, rotation_slot))

    # rename/move the input file
    from_path = paths.full_input_path
    to_path = paths.full_output_path(next_rotation_id)
    shutil.move(from_path, to_path)
    logging.info("Moved %s to %s" % (from_path, to_path))

    # remove old archives
    for f in to_delete:
        os.remove(f)
        logging.info("Removed %s" % f)

    # log the set of rotated files
    if verbose:
        logging.info("Current rotation set:")
        for f, d in _rotated_files(paths.output_path_no_ext):
            a_rotation_slot = algorithm.id_to_slot(d)
            logging.info("- %s / slot id %s" % (f, a_rotation_slot))


def rotate(algorithm, path, ext="", destination_dir=None, verbose=False):
    """
    Programmatic access to the archive rotator

    :param algorithm: an instance of BaseRotator from algorithms.py
    :param path: full path to input file
    :param ext: (optional) file extension to preserve
    :param destination_dir: (optional) different location for output file
    :param verbose: (optional) print more to stdout
    :return: nothing
    """
    paths = Paths(path, ext, destination_dir)
    _move_files(algorithm, paths, verbose)
