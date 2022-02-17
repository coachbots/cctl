# -*- coding: utf-8 -*-

"""
This module tests whether functions related to bot power and booting operate as
expected.
"""

import time
import unittest
import itertools
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api import bot_ctl as bc
from tests.feature import BotTestCase


class TestBootBot(BotTestCase):
    """Tests bot-power-related functions."""

    def test_boot(self):
        """Tests whether a robot can boot up and down successfully."""
        target_bot = self.random_testing_bot
        target_bot.boot(True)
        self.assert_bot_power(target_bot, True)

        target_bot.boot(False)
        self.assert_bot_power(target_bot, False)

    def test_boot_multiple(self):
        """Tests whether multiple bots can be booted up and down successfully.
        """
        bc.boot_bots(self.test_bots, True)
        self.assert_bot_powers(self.test_bots,
                               [True for _ in self.test_bots])

        bc.boot_bots(self.test_bots, False)
        self.assert_bot_powers(self.test_bots,
                               [False for _ in self.test_bots])

    def test_get_alives(self):
        """Tests whether get_alives operates as expected."""
        test_bots = self.test_bots[:3]
        bc.boot_bots(test_bots, True)

        start_time = time.time()
        self.assertEqual(sorted(test_bots), sorted(bc.get_alives()))
        self.assertLess(time.time() - start_time, 10,
                        'get_alives() failed being too slow.')


if __name__ == '__main__':
    unittest.main()
