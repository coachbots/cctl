#!/usr/bin/env python

import asyncio
import unittest
from cctl.api.cctld import CCTLDClient

from cctl.models import Coachbot

class TestBootBot(unittest.TestCase):
    def test_boots(self):
        async def __helper():
            async with CCTLDClient('tcp://127.0.0.1:16790') as client:
                await client.set_is_on(Coachbot(90, None), True)
        asyncio.get_event_loop().run_until_complete(__helper())
        result = input('Did the bot boot (Y/N)?')
        self.assertEqual('y', result.lower())

    def test_boots_down(self):
        async def __helper():
            async with CCTLDClient('tcp://127.0.0.1:16790') as client:
                await client.set_is_on(Coachbot(90, None), False)
        asyncio.get_event_loop().run_until_complete(__helper())
        result = input('Did the bot boot down (Y/N)?')
        self.assertEqual('y', result.lower())

