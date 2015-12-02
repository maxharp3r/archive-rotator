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


def _most_recent_rotated_file_or_none(path):
    """Looks for hanoi_rotator generated files in the passed-in path,
    returns the maximum rotation_id found.
    """
    rotated_files = [(a_path, rotation_id) for (a_path, rotation_id) in
                     _rotated_files(path)]
    if not rotated_files:
        return None
    else:
        highest_rotated_file = max(rotated_files, key=lambda x: x[1])
        return highest_rotated_file[1]


def _locate_files_to_delete(rotator, path, rotation_id):
    """Looks for hanoi_rotator generated files that occupy the same slot
    that will be given to rotation_id.
    """
    rotation_slot = rotator.id_to_slot(rotation_id)
    for a_path, a_rotation_id in [(p, n) for (p, n) in _rotated_files(path)]:
        if rotation_slot == rotator.id_to_slot(a_rotation_id):
            yield a_path


def rotate(algorithm, path, ext, verbose):
    # if a file extension was specified, trim it off the path
    path_without_ext = path if not ext else path.rsplit(ext, 1)[0]

    # find evidence of prior runs, reconstruct our rotation state from
    # the file names
    dir_name, file_name = os.path.split(path_without_ext)
    last_rotation_id = _most_recent_rotated_file_or_none(path_without_ext)
    next_rotation_id = \
        last_rotation_id + 1 if last_rotation_id is not None else 0
    to_delete = [p for p in _locate_files_to_delete(algorithm,
                                                    path_without_ext,
                                                    next_rotation_id)]
    if verbose:
        rotation_slot = algorithm.id_to_slot(next_rotation_id)
        logging.info("New file: rotation_id=%s, rotation_slot=%s"
                     % (next_rotation_id, rotation_slot))

    # rotate in the new file
    new_file_suffix = \
        FILE_NAME_TMPL % \
        {'datetime_str': datetime.now().strftime(DATETIME_FORMAT),
         'rotation_id': next_rotation_id,
         'ext': ext}
    new_path = os.path.join(dir_name, file_name + new_file_suffix)
    shutil.move(path, new_path)
    logging.info("Moved %s to %s" % (path, new_path))

    # remove old files
    for f in to_delete:
        os.remove(f)
        logging.info("Removed %s" % f)

    # log the set of rotated files
    if verbose:
        logging.info("Current rotation set:")
        for f, d in _rotated_files(path_without_ext):
            a_rotation_slot = algorithm.id_to_slot(d)
            logging.info("- %s / slot id %s" % (f, a_rotation_slot))
