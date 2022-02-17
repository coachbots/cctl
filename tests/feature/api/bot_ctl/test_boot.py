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
        bc.boot_bot(target_bot.identifier, True)
        self.wait_until_bots_reachable([target_bot])
        self.assert_bot_power(target_bot, True)

    def test_boot_negative(self):
        """Tests whether a robot can boot down successfully."""
        target_bot = self.random_testing_bot
        bc.boot_bot(target_bot.identifier, False)
        self.wait_until_bots_reachable([target_bot])
        self.assert_bot_power(target_bot, False)

    def test_boot_multiple_positive(self):
        """Tests whether multiple bots can boot up successfully."""
        bc.boot_bots((bot.identifier for bot in self.test_bots),
                     sum(1 for _ in self.test_bots) * [True])
        self.wait_until_bots_reachable(self.test_bots)
        self.assert_bot_powers(self.test_bots,
                               sum(1 for _ in self.test_bots) * [True])

    def test_boot_multiple_negative(self):
        """Tests whether multiple bots can be booted down successfully."""
        bc.boot_bots((bot.identifier for bot in self.test_bots), False)
        self.wait_until_bots_reachable(self.test_bots)
        self.assert_bot_powers(self.test_bots,
                               sum(1 for _ in self.test_bots) * [True])

    def test_get_alives(self):
        """Tests whether get_alives operates as expected."""
        target_bot = self.random_testing_bot
        bc.boot_bot(target_bot.identifier, True)
        self.wait_until_bots_reachable([target_bot])
        self.assertEqual([target_bot], list(bc.get_alives()))


if __name__ == '__main__':
    unittest.main()
