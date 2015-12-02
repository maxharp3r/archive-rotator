#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_archive_rotator
----------------------------------

Tests for `archive_rotator` module.
"""

import unittest

from archive_rotator.archive_rotator import \
    SimpleRotator, HanoiRotator, TieredRotator


class TestArchiveRotator(unittest.TestCase):

    def test_simple_rotator_assignment(self):
        self.assertEqual(SimpleRotator(4).id_to_slot(0), 0)
        self.assertEqual(SimpleRotator(4).id_to_slot(7), 3)

    def test_hanoi_rotator_assignment(self):
        # The first backup (id 0) should be assigned the biggest slot
        # available: 2^(n-1)
        self.assertEqual(HanoiRotator(3).id_to_slot(0), 4)
        self.assertEqual(HanoiRotator(4).id_to_slot(0), 8)
        self.assertEqual(HanoiRotator(5).id_to_slot(0), 16)

        self.assertEqual(HanoiRotator(4).id_to_slot(1), 1)
        self.assertEqual(HanoiRotator(4).id_to_slot(3), 1)
        self.assertEqual(HanoiRotator(4).id_to_slot(9), 1)
        self.assertEqual(HanoiRotator(4).id_to_slot(2), 2)
        self.assertEqual(HanoiRotator(4).id_to_slot(18), 2)
        self.assertEqual(HanoiRotator(4).id_to_slot(4), 4)
        self.assertEqual(HanoiRotator(4).id_to_slot(8), 8)
        self.assertEqual(HanoiRotator(4).id_to_slot(24), 8)

        self.assertEqual(HanoiRotator(5).id_to_slot(16), 16)
        self.assertEqual(HanoiRotator(5).id_to_slot(30), 2)
        self.assertEqual(HanoiRotator(5).id_to_slot(32), 16)

        self.assertEqual(HanoiRotator(6).id_to_slot(32), 32)

    def test_tiered_rotator_assignment(self):
        self.assertEqual(TieredRotator([2, 2]).id_to_slot(0), 0)
        self.assertEqual(TieredRotator([2, 2]).id_to_slot(1), 1)
        self.assertEqual(TieredRotator([2, 2]).id_to_slot(2), 2)
        self.assertEqual(TieredRotator([2, 2]).id_to_slot(8), 2)
        self.assertEqual(TieredRotator([2, 2]).id_to_slot(9), 0)

        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(0), 0)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(1), 1)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(4), 4)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(5), 0)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(19), 19)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(39), 39)

        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(10), 0)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(24), 4)
        self.assertEqual(TieredRotator([4, 3, 2]).id_to_slot(59), 19)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
