# -*- coding: utf-8 -*-

"""
This module holds the base class used for Bot feature testing.
"""

from time import time
from typing import Generator, Iterable
import unittest
import random
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api.bot_ctl import Coachbot


class BotTestCase(unittest.TestCase):
    """Represents a base Bot-related integration test case."""

    @property
    def test_bots(self) -> Generator[Coachbot, None, None]:
        """
        Returns:
            Generator[Coachbot, None, None]: The testing bots.
        """
        return (Coachbot(90 + x) for x in range(0, 10))

    @property
    def test_bot_ids(self) -> Generator[int, None, None]:
        """
        Returns:
            Generator[int, None, None]: The testing bots' ids.
        """
        return (bot.identifier for bot in self.test_bots)

    @property
    def random_testing_bot(self) -> Coachbot:
        """
        Returns:
            Coachbot: A random testing bot.
        """
        return random.choice(list(self.test_bots))

    @property
    def random_testing_bot_id(self) -> int:
        """
        Returns:
            int: A random testing bot.
        """
        return self.random_testing_bot.identifier

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
                              states: Iterable[bool],
                              timeout: float = 10) -> None:
        """Pauses execution until all specified bots are reachable.

        Parameters:
            bots (Iterable[Coachbot]): The target bots.
            states (Iterable[bool]): The expected states of the bots.
            timeout (float): The maximum allowable timeout.
        """
        as_expected = False
        start_time = time()
        while not as_expected and (time() - start_time) < timeout:
            for bot, expected_state in zip(bots, states):
                if bot.is_alive() != expected_state:
                    as_expected = False
                    break
                as_expected = True
