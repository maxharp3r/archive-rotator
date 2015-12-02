#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_algorithms
---------------

Tests for `archive_rotator.algorithms` module.
"""

import unittest

from archive_rotator import rotator
from archive_rotator.algorithms import \
    SimpleRotator, HanoiRotator, TieredRotator


class TestRotator(unittest.TestCase):

    def test_rotated_files(self):
        foo = [x for x in rotator._rotated_files("tests/test_dir_a/mydump")]
        self.assertGreater(len(foo), 0)

    def test_foo(self):
        algorithm = SimpleRotator(3, False)
        self.assertEqual(1, 1)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
