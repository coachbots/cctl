#!/usr/bin/env python

import asyncio
import logging
from typing import Iterable, AsyncGenerator
from bleak import BleakError, BleakDBusError
from cctl.models import Coachbot
from cctl.protocols.ble import BluefruitMode
from .client import CoachbotBLEClient
from .errors import BLENotReachableError


async def boot_bots(
    bots: Iterable[Coachbot],
    state: bool) -> AsyncGenerator[BLENotReachableError, None]:
    """Attempts to boot the given iterable MAC addresses up.

    Parameters:
        bot_macs (Iterable[Coachbot]): The MAC addresses to attempt to boot up.
        state (bool): The state to attempt to boot to. If True, the bots turn
            on, otherwise they turn off.

    Returns:
        A generator of ``BLENotReachableError`` objects which can be used to
        figure out which robots could not be booted up.
    """
    max_attempts = 5

    queue = asyncio.Queue()

    for bot in bots:
        await queue.put((bot, bot.bluetooth_mac_address, 0))

    while not queue.empty():
        bot, addr, attempts = await queue.get()
        try:
            async with CoachbotBLEClient(addr, pair=True,
                                         timeout=10) as client:
                await client.set_mode(BluefruitMode(True))
                await client.set_mode_led(state)
                await client.set_mode(BluefruitMode(False))
                logging.getLogger('bluetooth').debug(
                    'Successfully booted bot %s', addr)
        except (BleakError, BleakDBusError, asyncio.TimeoutError) as err:
            if attempts < max_attempts:
                logging.getLogger('bluetooth').warning(
                    'Could not command %s due to %s. Will Retry...',
                    addr, err)
                await queue.put((bot, addr, attempts + 1))
            else:
                logging.getLogger('bluetooth').error(
                    'Could not command %s after %d attempts. Giving Up.',
                    addr, max_attempts)
                yield BLENotReachableError(bot)
