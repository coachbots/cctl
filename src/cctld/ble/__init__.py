#!/usr/bin/env python

"""This exposes the BLE functions to CCTLD."""

from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Iterable, AsyncGenerator, Tuple
from subprocess import Popen
import asyncio
import logging

from bleak.exc import BleakError, BleakDBusError

from cctl.models import Coachbot
from cctl.protocols.ble import BluefruitMode

from .client import CoachbotBLEClient
from .errors import BLENotReachableError


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.0.13'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


class BleManager:
    """Manages BLE transactions."""

    def __init__(self, avail_interfaces: Iterable[int]) -> None:
        """Manages BLE transactions.

        Parameters:
            avail_interfaces (Iterable[int]): The interfaces that this manager
            has access to. These interfaces must be integers and correspond to
            the numbers that ``hciconfig`` will return.
        """
        intfcs = list(avail_interfaces)
        self.queue: asyncio.Queue[int] = asyncio.Queue(maxsize=len(intfcs))
        for intf in intfcs:
            self.queue.put_nowait(intf)

    @asynccontextmanager
    async def transaction(self):
        """Yields an interface for use with transactions.

        Blocks until a transaction is available.
        """
        intfc = await self.queue.get()
        try:
            yield intfc
        finally:
            await self.queue.put(intfc)

    async def boot_bots(
        self,
        bots: Iterable[Coachbot],
        state: bool
    ) -> AsyncGenerator[BLENotReachableError, None]:
        """Attempts to boot the given iterable MAC addresses up.

        Parameters:
            ble_info (BleInfo): The BleInfo of the AppState.
            bot_macs (Iterable[Coachbot]): The MAC addresses to attempt to boot
            up. state (bool): The state to attempt to boot to. If True, the
            bots turn on, otherwise they turn off.

        Returns:
            A generator of ``BLENotReachableError`` objects which can be used
            to figure out which robots could not be booted up.
        """
        max_attempts = 5

        async def boot_bot(addr: str) -> None:
            """Boots a bot at a specified BLE MAC address, blocking until an
            interface is available.
            """
            async with self.transaction() as intf:
                # TODO: Ideally this call shouldn't be necessary, but it's
                # difficult to get stuff to work without it.
                Popen(['hciconfig', f'hci{intf}', 'down']).wait()
                Popen(['hciconfig', f'hci{intf}', 'up']).wait()
                async with CoachbotBLEClient(
                    addr, pair=True, timeout=10,
                    adapter=f'hci{intf}'
                ) as client:
                    await client.set_mode(BluefruitMode(True))
                    await client.set_mode_led(state)
                    await client.set_mode(BluefruitMode(False))
                    logging.getLogger('bluetooth').debug(
                        'Successfully booted bot %s', addr)

        bot_queue: asyncio.Queue[Tuple[Coachbot, int]] = asyncio.Queue()
        for bot in bots:
            await bot_queue.put((bot, 0))

        while not bot_queue.empty():
            bot, attempts = await bot_queue.get()
            addr = bot.bluetooth_mac_address

            try:
                # Spawn a task to boot a bot. This function will get fired for
                # all possible bots but will block its own internal execution
                # until an interface is available.
                await boot_bot(addr)
            except (BleakError, BleakDBusError, asyncio.TimeoutError) as err:
                if attempts < max_attempts:
                    logging.getLogger('bluetooth').warning(
                        'Could not command %s due to %s. Will Retry...',
                        addr, err)
                    await bot_queue.put((bot, attempts + 1))
                else:
                    logging.getLogger('bluetooth').error(
                        'Could not command %s after %d attempts. Giving Up.',
                        addr, max_attempts)
                    yield BLENotReachableError(bot)
