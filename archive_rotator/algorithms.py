#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
archive_rotator.algorithms
--------------------------

Rotation algorithms are defined here.
"""

import abc
import logging


class RotatorBase(object):
    """
    Rotator interface.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def id_to_slot(self, rotation_id):
        """Given a backup id, assign a rotation slot."""
        return


class SimpleRotator(RotatorBase):
    """FIFO implementation."""

    def __init__(self, num_rotation_slots, verbose=False):
        self.num_rotation_slots = num_rotation_slots
        if verbose:
            logging.info("Rotation slots are: %s" % range(num_rotation_slots))

    def id_to_slot(self, rotation_id):
        return rotation_id % self.num_rotation_slots


class HanoiRotator(RotatorBase):
    """Tower of Hanoi implementation.
    A backup slot is a power of two (1, 2, 4, 8, ...).
    """

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

        # find the maximum power of two that divides cleanly into
        # (rotation_id % max_rotation_slot)
        max_divisor = 1
        for divisor in (2 ** n for n in range(1, self.num_rotation_slots + 1)):
            if adjusted_rotation_id % divisor == 0:
                max_divisor = divisor
            else:
                break
        return max_divisor


class TieredRotator(RotatorBase):
    """Tiered rotation schedule.

    This is a generalization of the grandfather-father-son rotation algorithm.
    """

    def __init__(self, tier_sizes, verbose=False):
        self.num_tiers = len(tier_sizes)
        self.biggest_tier = self.num_tiers - 1
        self.tiers = []
        self.multipliers = []

        # given a list of tier sizes, configure a list of multipliers,
        # and a list of tiers with slots
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
            # divide the rotation_id by the multiplier .. if it is equal to
            # the multiplier-1, then we've found our slot
            (quotient, remainder) = divmod(rotation_id, self.multipliers[i])
            if remainder == (self.multipliers[i] - 1):
                # wrap within a tier (based on how many slots in the tier) to
                # prevent unlimited growth the top tier is a special case -
                # other tiers skip every nth run to promote to a higher tier
                modifier = len(self.tiers[i]) \
                    if (i == self.biggest_tier) \
                    else len(self.tiers[i]) + 1
                modified_quotient = quotient % modifier
                slot = modified_quotient \
                    * self.multipliers[i] \
                    + (self.multipliers[i] - 1)
                break
        return slot

