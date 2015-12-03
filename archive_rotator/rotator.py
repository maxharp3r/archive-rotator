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


def _get_now():
    # XXX: this is here to facilitate mocking in unit tests
    return datetime.now()


def _build_output_path(path_without_ext, ext, next_rotation_id):
    """Build the output filename
    """
    assert not ext or not path_without_ext.endswith(ext)

    dir_name, file_name = os.path.split(path_without_ext)
    new_file_suffix = \
        FILE_NAME_TMPL % \
        {'datetime_str': _get_now().strftime(DATETIME_FORMAT),
         'rotation_id': next_rotation_id,
         'ext': ext}
    return os.path.join(dir_name, file_name + new_file_suffix)


def rotate(algorithm, path, ext, verbose):
    # if a file extension was specified, trim it off the path
    # we do not try to guess file extensions, only use if explicitly configured
    path_without_ext = path if not ext else path.rsplit(ext, 1)[0]

    # reconstruct rotation state from the file names in output dir
    rotated_files = list(_rotated_files(path_without_ext))
    next_rotation_id = _next_rotation_id(rotated_files)
    to_delete = list(_locate_files_to_delete(algorithm,
                                             rotated_files,
                                             next_rotation_id))
    if verbose:
        rotation_slot = algorithm.id_to_slot(next_rotation_id)
        logging.info("New file: rotation_id=%s, rotation_slot=%s"
                     % (next_rotation_id, rotation_slot))

    # rename/move the input file
    new_path = _build_output_path(path_without_ext, ext, next_rotation_id)
    shutil.move(path, new_path)
    logging.info("Moved %s to %s" % (path, new_path))

    # remove old archives
    for f in to_delete:
        os.remove(f)
        logging.info("Removed %s" % f)

    # log the set of rotated files
    if verbose:
        logging.info("Current rotation set:")
        for f, d in rotated_files:
            a_rotation_slot = algorithm.id_to_slot(d)
            logging.info("- %s / slot id %s" % (f, a_rotation_slot))
