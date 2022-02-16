# -*- coding: utf-8 -*-

"""
This module tests whether functions related to bot power and booting operate as
expected.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api import bot_ctl as bc
from tests.feature import BotTestCase


class TestBootBot(BotTestCase):
    """Tests bot-power-related functions."""

    def test_boot_positive(self):
        """Tests whether a robot can boot up successfully."""
        target_bot = self.random_testing_bot
        bc.boot_bot(target_bot, True)
        self.assert_bot_power(target_bot, True)

    def test_boot_negative(self):
        """Tests whether a robot can boot down successfully."""
        target_bot = self.random_testing_bot
        bc.boot_bot(target_bot, False)
        self.assert_bot_power(target_bot, False)

    def test_boot_multiple_positive(self):
        """Tests whether multiple bots can boot up successfully."""
        bc.boot_bots(self.test_bots, len(self.test_bots) * [True])
        self.assert_bot_powers(self.test_bots, len(self.test_bots) * [True])

    def test_boot_multiple_negative(self):
        """Tests whether multiple bots can be booted down successfully."""
        bc.boot_bots(self.test_bots, False)
        self.assert_bot_powers(self.test_bots, len(self.test_bots) * [True])

    def test_get_alives(self):
        """Tests whether get_alives operates as expected."""
        target_bot = self.random_testing_bot
        bc.boot_bot(target_bot, True)

        coachbot = bc.Coachbot(target_bot)
        self.assertEqual([coachbot], list(bc.get_alives(
            bc.Coachbot(i) for i in self.test_bots)))


if __name__ == '__main__':
    unittest.main()
