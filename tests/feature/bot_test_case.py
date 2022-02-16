# -*- coding: utf-8 -*-

"""
This module holds the base class used for Bot feature testing.
"""

from typing import Iterable, List
import unittest
import random

from cctl.api.bot_ctl import Coachbot


class BotTestCase(unittest.TestCase):
    """Represents a base Bot-related integration test case."""

    @property
    def test_bots(self) -> List[int]:
        """
        The identifiers of testing bots.
        """
        return [90 + x for x in range(0, 10)]

    @property
    def random_testing_bot(self) -> int:
        """
        Returns:
            A random testing bot.
        """
        return random.choice(self.test_bots)

    def assert_bot_power(self, bot_id: int, expected: bool):
        """
        Asserts that a bot is turned on or off.

        Parameters:
            bot_id: The id of the bot.
            expected: The expected state of the bot.
        """

    def assert_bot_powers(self, bot_ids: List[int], expecteds: List[bool]):
        """
        Asserts that multiple bots are turned on or off.

        Parameters:
            bot_ids: A list of bot ids.
            expecteds: A list of expected states for each of the bots.
        """
        for bot_id, expected in zip(bot_ids, expecteds):
            self.assert_bot_power(bot_id, expected)
