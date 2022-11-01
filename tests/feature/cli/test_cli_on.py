#!/usr/bin/env python3

import sys
import os
import subprocess as sproc
from cctl.models.coachbot import Coachbot

from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))


class TestOnCommands(BotTestCase):
    """Tests whether `cctl on` commands behave as expected."""
    async def test_on_singular(self):
        """Tests `cctl on 9` returns a successful code. """
        result = sproc.run(['cctl',
                            'on',
                            str(self.random_testing_bot.identifier)])
        self.assertEqual(0, result.returncode)
        await self.assert_bot_power(Coachbot.stateless(9), True)

    async def test_on_range_90_99(self):
        """Tests `cctl on 30-34` returns a success code."""
        result = sproc.run([
            'cctl', 'on',
            str(' '.join([str(b.identifier) for b in self.test_bots]))])
        self.assertEqual(0, result.returncode)
        for i in range(90, 99):
            await self.assert_bot_power(Coachbot.stateless(i), True)

    async def test_on_overflow(self):
        """Tests `cctl on 101` returns an error code."""
        result = sproc.run(['cctl', 'on', '101'])
        self.assertNotEqual(0, result.returncode)

    async def test_on_float(self):
        """Tests whether `cctl on 2.3` returns an error code."""
        result = sproc.run(['cctl', 'on', '2.3'])
        self.assertNotEqual(0, result.returncode)

    async def test_on_multiple(self):
        """Tests whether `cctl on 59 60 68` returns a success code."""
        result = sproc.run(['cctl', 'on', '59', '60', '68'])
        self.assertEqual(0, result.returncode)
        for i in [59, 60, 68]:
            await self.assert_bot_power(Coachbot.stateless(i), True)

    async def test_on_combination(self):
        """Tests whether `cctl on 21 25-27 38` returns a success code."""
        result = sproc.run(['cctl', 'on', '21', '25-27', '38'])
        self.assertEqual(0, result.returncode)
        for i in [21, 25, 26, 27, 38]:
            await self.assert_bot_power(Coachbot.stateless(i), True)

    async def test_on_underflow(self):
        """Tests `cctl on -1` returns an error code."""
        result = sproc.run(['cctl', 'on', '-1'])
        self.assertNotEqual(0, result.returncode)
