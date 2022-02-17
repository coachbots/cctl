# -*- coding: utf-8 -*-

"""
This module holds the base class used for Bot feature testing.
"""

from time import time
from typing import Generator, Iterable, List
import unittest
import random
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api.bot_ctl import Coachbot, boot_bots, wait_until_bots_state


class BotTestCase(unittest.TestCase):
    """Represents a base Bot-related integration test case.

    You can inherit from this test case in order to receive useful methods as
    well ensure that all bots start and end in a booted-down state.
    """

    def setUp(self) -> None:
        super().setUp()
        boot_bots('all', False)

    def tearDown(self) -> None:
        super().tearDown()
        boot_bots('all', False)

    @property
    def test_bots(self) -> List[Coachbot]:
        """
        Returns:
            Generator[Coachbot, None, None]: The testing bots.
        """
        return [Coachbot(90 + x) for x in range(0, 10)]

    @property
    def random_testing_bot(self) -> Coachbot:
        """
        Returns:
            Coachbot: A random testing bot.
        """
        return random.choice(list(self.test_bots))

    def assert_bot_power(self, bot: Coachbot, expected: bool):
        """
        Asserts that a bot is turned on or off.

        Parameters:
            bot_id: The id of the bot.
            expected: The expected state of the bot.
        """
        self.assertEqual(expected, bot.is_alive())

    def assert_bot_powers(self, bots: Iterable[Coachbot],
                          expecteds: Iterable[bool]):
        """
        Asserts that multiple bots are turned on or off.

        Parameters:
            bots (Iterable[Coachbot]): An iterable of Coachbots.
            expecteds (Iterable[Bool]): An iterable of expected states for each
                of the bots.
        """
        for bot, expected in zip(bots, expecteds):
            self.assert_bot_power(bot, expected)

    def wait_until_bots_state(self, bots: Iterable[Coachbot],
                              states: Iterable[bool]) -> None:
        """Pauses execution until all specified bots are reachable.

        Parameters:
            bots (Iterable[Coachbot]): The target bots.
            states (Iterable[bool]): The expected states of the bots.
            timeout (float): The maximum allowable timeout.
        """
        wait_until_bots_state(bots, states)
