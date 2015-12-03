#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_integration
----------------

Integration tests. These do not cover the CLI.
"""

import contextlib
import os
import shutil
import tempfile
import unittest

from archive_rotator import rotator
from archive_rotator.algorithms import SimpleRotator, HanoiRotator


ARCHIVE_NAME = "dump.tar.gz"
EXT = ".tar.gz"


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def num_archives(temp_dir):
    return len([name for name in os.listdir(temp_dir)
                if os.path.isfile(os.path.join(temp_dir, name))])


def create_test_archive(temp_dir):
    path = os.path.join(temp_dir, ARCHIVE_NAME)
    with open(path, 'a'):
        os.utime(path, None)
    return path


class IntegrationTest(unittest.TestCase):

    def test_integration_many_iterations(self):
        with make_temp_directory() as temp_dir:
            self.assertEqual(num_archives(temp_dir), 0)
            for i in range(3):
                paths = rotator.Paths(create_test_archive(temp_dir), "", None)
                rotator.rotate(SimpleRotator(5), paths, False)
            self.assertEqual(num_archives(temp_dir), 3)
            for i in range(100):
                paths = rotator.Paths(create_test_archive(temp_dir), "", None)
                rotator.rotate(SimpleRotator(5), paths, False)
            self.assertEqual(num_archives(temp_dir), 5)

    def test_integration_with_ext(self):
        with make_temp_directory() as temp_dir:
            self.assertEqual(num_archives(temp_dir), 0)
            for i in range(3):
                paths = rotator.Paths(create_test_archive(temp_dir), EXT, None)
                rotator.rotate(SimpleRotator(20), paths, False)
            self.assertEqual(num_archives(temp_dir), 3)
            for i in range(100):
                paths = rotator.Paths(create_test_archive(temp_dir), EXT, None)
                rotator.rotate(SimpleRotator(20), paths, False)
            self.assertEqual(num_archives(temp_dir), 20)

    def test_integration_with_hanoi(self):
        with make_temp_directory() as temp_dir:
            self.assertEqual(num_archives(temp_dir), 0)
            for i in range(3):
                paths = rotator.Paths(create_test_archive(temp_dir), EXT, None)
                rotator.rotate(HanoiRotator(20), paths, False)
            self.assertEqual(num_archives(temp_dir), 3)
            for i in range(100):
                paths = rotator.Paths(create_test_archive(temp_dir), EXT, None)
                rotator.rotate(HanoiRotator(20), paths, False)
            # 1, 2, 4, 8, 16, 32, 64, 128 (first archive gets 128)
            self.assertEqual(num_archives(temp_dir), 8)

    def test_integration_with_destination_dir(self):
        with make_temp_directory() as temp_dir, \
                make_temp_directory() as temp_output_dir:
            self.assertEqual(num_archives(temp_dir), 0)
            self.assertEqual(num_archives(temp_output_dir), 0)
            for i in range(3):
                paths = rotator.Paths(create_test_archive(temp_dir), EXT,
                                      temp_output_dir)
                rotator.rotate(SimpleRotator(5), paths, False)
            self.assertEqual(num_archives(temp_dir), 0)
            self.assertEqual(num_archives(temp_output_dir), 3)
            for i in range(100):
                paths = rotator.Paths(create_test_archive(temp_dir), EXT,
                                      temp_output_dir)
                rotator.rotate(SimpleRotator(5), paths, False)
            self.assertEqual(num_archives(temp_dir), 0)
            self.assertEqual(num_archives(temp_output_dir), 5)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
