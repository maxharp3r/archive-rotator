#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_rotator
------------

Tests for `archive_rotator.rotator` module.
"""

from datetime import datetime
import unittest

from archive_rotator import rotator
from archive_rotator.algorithms import SimpleRotator


def mocked_get_now():
    """
    A method to call instead of datetime.now() to ensure testing stability
    """
    return datetime(2012, 1, 1, 10, 10, 10)


class TestPaths(unittest.TestCase):

    def test_path_parsing(self):
        paths = rotator.Paths("/a/b/~c/a.b.c", "", None)
        self.assertEqual(paths.input_dir, "/a/b/~c")
        self.assertEqual(paths.input_fn, "a.b.c")
        self.assertEqual(paths.input_ext, "")
        self.assertEqual(paths.output_dir, "/a/b/~c")

        paths = rotator.Paths("./a/b/~c/a.b.c", ".c", "/d/e/f/")
        self.assertEqual(paths.input_dir, "./a/b/~c")
        self.assertEqual(paths.input_fn, "a.b")
        self.assertEqual(paths.input_ext, ".c")
        self.assertEqual(paths.output_dir, "/d/e/f/")

    def test_property_fields(self):
        paths = rotator.Paths("/a/b/~c/a.b.c", "", None)
        self.assertEqual(paths.full_input_path, "/a/b/~c/a.b.c")
        self.assertEqual(paths.output_path_no_ext, "/a/b/~c/a.b.c")

        paths = rotator.Paths("/a/b/~c/a.b.c", ".b.c", "/d/e/f/")
        self.assertEqual(paths.full_input_path, "/a/b/~c/a.b.c")
        self.assertEqual(paths.output_path_no_ext, "/d/e/f/a")

    def test_build_output_path1(self):
        """
        no ext, no output dir, easy path
        """
        paths = rotator.Paths("foo/a.zip", "", None)
        paths._get_now = mocked_get_now

        self.assertEqual(paths.full_output_path(0),
                         "foo/a.zip.2012-01-01-101010.backup-0")

        self.assertEqual(paths.full_output_path(128),
                         "foo/a.zip.2012-01-01-101010.backup-128")

    def test_build_output_path2(self):
        """
        no ext, no output dir, harder path
        """
        paths = rotator.Paths("/a/b/~c/a.b.c", "", None)
        paths._get_now = mocked_get_now
        self.assertEqual(paths.full_output_path(0),
                         "/a/b/~c/a.b.c.2012-01-01-101010.backup-0")

    def test_build_output_path3(self):
        """
        ext, no output dir, harder path
        """
        paths = rotator.Paths("/a/b/~c/a.b.c", ".b.c", None)
        paths._get_now = mocked_get_now
        self.assertEqual(paths.full_output_path(0),
                         "/a/b/~c/a.2012-01-01-101010.backup-0.b.c")

    def test_build_output_path4(self):
        """
        no ext, output dir, harder path
        """
        paths = rotator.Paths("/a/b/~c/a.b.c", "", "/foo/bar")
        paths._get_now = mocked_get_now
        self.assertEqual(paths.full_output_path(0),
                         "/foo/bar/a.b.c.2012-01-01-101010.backup-0")


class TestRotator(unittest.TestCase):

    def test_finds_rotated_files(self):
        rotated_files = list(rotator._rotated_files("tests/test_dir_a/mydump"))
        self.assertEqual(len(rotated_files), 5)

        first_path, first_rotation_id = rotated_files[0]
        # no guaranteed order to the globbing, so this cannot verify exactly
        self.assertRegexpMatches(
            first_path,
            "tests\/test_dir_a\/mydump.*2015-12-02.*\.backup-[3-7].*")
        self.assertGreaterEqual(first_rotation_id, 3)

    def test_rotated_files_respects_name(self):
        # there are no files matching "another_name"
        rotated_files = list(rotator._rotated_files("tests/test_dir_a/foo"))
        self.assertEqual(len(rotated_files), 0)

    def test_finds_next_rotation_id(self):
        rotated_files = list(rotator._rotated_files("tests/test_dir_a/mydump"))
        x = rotator._next_rotation_id(rotated_files)
        self.assertEqual(x, 8)

    def test_next_rotation_id_is_0_without_match(self):
        rotated_files = list(rotator._rotated_files("tests/test_dir_a/foo"))
        x = rotator._next_rotation_id(rotated_files)
        self.assertEqual(x, 0)

    def test_locate_files_to_delete(self):
        rotated_files = list(rotator._rotated_files("tests/test_dir_a/mydump"))

        # 5 slots
        to_delete = list(rotator._locate_files_to_delete(
            SimpleRotator(5), rotated_files, 8))
        self.assertEqual(len(to_delete), 1)

        # 10 slots (don't delete anything)
        to_delete = list(rotator._locate_files_to_delete(
            SimpleRotator(10), rotated_files, 8))
        self.assertEqual(len(to_delete), 0)

        # 2 slots (delete a #4 and #6)
        to_delete = list(rotator._locate_files_to_delete(
            SimpleRotator(2), rotated_files, 8))
        self.assertEqual(len(to_delete), 2)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
