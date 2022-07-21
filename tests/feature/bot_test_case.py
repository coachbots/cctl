# -*- coding: utf-8 -*-

"""
This module holds the base class used for Bot feature testing.
"""

from typing import Generator, Iterable, List
import unittest
import random
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.models.coachbot import Coachbot, CoachbotState
from cctl.api.cctld import CCTLDClient


class BotTestCase(unittest.IsolatedAsyncioTestCase):
    """Represents a base Bot-related integration test case.

    You can inherit from this test case in order to receive useful methods as
    well ensure that all bots start and end in a booted-down state.
    """

    @property
    def cctld_req_serv(self) -> str:
        return 'tcp://localhost:16790'

    async def asyncSetUp(self) -> None:
        async with CCTLDClient(self.cctld_req_serv) as client:
            await client.set_is_on('all', False)

    async def asyncTearDown(self) -> None:
        async with CCTLDClient(self.cctld_req_serv) as client:
            await client.set_is_on('all', False)

    @property
    def test_bots(self) -> Generator[Coachbot, None, None]:
        """
        Returns:
            Generator[Coachbot, None, None]: The testing bots.
        """
        return (Coachbot(90 + x, CoachbotState(None)) for x in range(0, 10))

    @property
    def random_testing_bot(self) -> Coachbot:
        """
        Returns:
            Coachbot: A random testing bot.
        """
        return random.choice(list(self.test_bots))

    async def assert_bot_power(self, bot: Coachbot, expected: bool):
        """
        Asserts that a bot is turned on or off.

        Parameters:
            bot: The target Coachbot
            expected: The expected state of the bot.
        """
        async with CCTLDClient(self.cctld_req_serv) as client:
            bot_state = await client.read_state(bot)
            self.assertEqual(expected, bot_state.is_on)

    async def assert_bot_state(self, bot: Coachbot, expected: CoachbotState):
        """Asserts that a bot state is as expected.

        Parameters:
            bot: The target bot.
            expected (CoachbotState): The expected coachbot state.
        """
        async with CCTLDClient(self.cctld_req_serv) as client:
            bot_state = await client.read_state(bot)
            self.assertEqual(expected, bot_state)
