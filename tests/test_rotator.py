#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_rotator
------------

Tests for `archive_rotator.rotator` module.
"""

import unittest

from archive_rotator import rotator
from archive_rotator.algorithms import SimpleRotator


class TestRotator(unittest.TestCase):

    def test_finds_rotated_files(self):
        rotated_files = list(rotator._rotated_files("tests/test_dir_a/mydump"))
        self.assertEqual(len(rotated_files), 5)
        first_path, first_rotation_id = rotated_files[0]
        self.assertEqual(
            first_path,
            "tests/test_dir_a/mydump.2015-12-02-161558.backup-3.tgz")
        self.assertEqual(first_rotation_id, 3)

    def test_rotated_files_respects_name(self):
        # there are no files matching "another_name"
        rotated_files = \
            list(rotator._rotated_files("tests/test_dir_a/another_name"))
        self.assertEqual(len(rotated_files), 0)

    def test_finds_max_rotation_id(self):
        x = rotator._max_rotation_id("tests/test_dir_a/mydump")
        self.assertEqual(x, 7)

    def test_max_rotation_id_is_none_without_match(self):
        x = rotator._max_rotation_id("tests/test_dir_a/another_name")
        self.assertEqual(x, None)

    def test_locate_files_to_delete(self):
        # 5 slots
        to_delete = list(rotator._locate_files_to_delete(
            SimpleRotator(5), "tests/test_dir_a/mydump", 8))
        self.assertEqual(len(to_delete), 1)

        # 10 slots (don't delete anything)
        to_delete = list(rotator._locate_files_to_delete(
            SimpleRotator(10), "tests/test_dir_a/mydump", 8))
        self.assertEqual(len(to_delete), 0)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
