#!/usr/bin/env python3

import sys
import os
import subprocess as sproc
from cctl.models.coachbot import Coachbot

from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))


class TestOnCommands(BotTestCase):
    """Tests whether `cctl off` commands behave as expected."""
    async def test_off_singular(self):
        """Tests `cctl off 9` returns a successful code. """
        result = sproc.run(['cctl',
                            'on',
                            str(self.random_testing_bot.identifier)])
        self.assertEqual(0, result.returncode)
        await self.assert_bot_power(Coachbot.stateless(9), False)

    async def test_off_range(self):
        """Tests `cctl off x-y` returns a success code."""
        result = sproc.run([
            'cctl', 'on',
            str(' '.join([str(b.identifier) for b in self.test_bots]))])
        self.assertEqual(0, result.returncode)
        for i in range(30, 35):
            await self.assert_bot_power(Coachbot.stateless(i), False)

    async def test_off_overflow(self):
        """Tests `cctl off 101` returns an error code."""
        result = sproc.run(['cctl', 'off', '101'])
        self.assertNotEqual(0, result.returncode)

    async def test_off_float(self):
        """Tests whether `cctl off 2.3` returns an error code."""
        result = sproc.run(['cctl', 'off', '2.3'])
        self.assertNotEqual(0, result.returncode)

    async def test_off_multiple(self):
        """Tests whether `cctl off 59 60 68` returns a success code."""
        result = sproc.run(['cctl', 'off', '59', '60', '68'])
        self.assertEqual(0, result.returncode)
        for i in [59, 60, 68]:
            await self.assert_bot_power(Coachbot.stateless(i), False)

    async def test_off_combinatioff(self):
        """Tests whether `cctl off 21 25-27 38` returns a success code."""
        result = sproc.run(['cctl', 'off', '21', '25-27', '38'])
        self.assertEqual(0, result.returncode)
        for i in [21, 25, 26, 27, 38]:
            await self.assert_bot_power(Coachbot.stateless(i), False)

    async def test_off_underflow(self):
        """Tests `cctl off -1` returns an error code."""
        result = sproc.run(['cctl', 'off', '-1'])
        self.assertNotEqual(0, result.returncode)
