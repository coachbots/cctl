#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Holds the Coachbot unit test cases."""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api.bot_ctl import Coachbot


class TestCoachbot(unittest.TestCase):
    """TestCase for the Coachbot class.

    Note:
        This TestCase only runs unit tests.
    """

    def errors_out_on_invalid_range(self):
        """Ensures that a Coachbot cannot be constructed with an invalid id."""
        with self.assertRaises(ValueError):
            Coachbot(100)

    def test_correct_address(self):
        """Tests whether the correct IP address is returned for a coachbot."""
        self.assertEqual('192.168.1.93', Coachbot(90).address)

    def test_can_be_built_from_address(self):
        """Tests whether the coachbot can be constructed form an IP address."""
        self.assertEqual(Coachbot(90), Coachbot.from_address('192.168.1.93'))


if __name__ == '__main__':
    unittest.main()
