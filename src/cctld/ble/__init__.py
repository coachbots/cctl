#!/usr/bin/env python

"""This exposes the BLE functions to CCTLD."""

from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Iterable, AsyncGenerator, Tuple, List
from asyncio.subprocess import create_subprocess_exec
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
        # This implementation relies on two types of attempts -- soft attempts
        # and hard attempts. Soft attempts are attempts that can possibly be
        # fixed by retrying to send the same BLE-UART command again. These
        # usually address periodic unreachability.
        # Hard attempts are attempts that reset the whole bluetooth service on
        # failure. These are very slow and should be used sparingly.
        max_soft_attempts = 3
        hard_reset_attempts = 4

        async def boot_bot(addr: str) -> None:
            """Boots a bot at a specified BLE MAC address, blocking until an
            interface is available.
            """
            async with self.transaction() as intf:
                logging.getLogger('bluetooth').debug(
                    'Attempting to command %s via interface %s',
                    addr, f'hci{intf}')
                async with CoachbotBLEClient(
                    addr, pair=True, timeout=10,
                    adapter=f'hci{intf}'
                ) as client:
                    await client.set_mode(BluefruitMode(True))
                    await client.set_mode_led(state)
                    await client.set_mode(BluefruitMode(False))
                    logging.getLogger('bluetooth').debug(
                        'Successfully booted bot %s', addr)

        async def boot_from_q(bot: Coachbot,
                              attempts: int,
                              soft_err_q: asyncio.Queue[Tuple[Coachbot, int]],
                              hard_err_q: asyncio.Queue[Coachbot]):
            addr = bot.bluetooth_mac_address

            try:
                # Spawn a task to boot a bot. This function will get fired for
                # all possible bots but will block its own internal execution
                # until an interface is available.
                await boot_bot(addr)
            except (BleakError, BleakDBusError,
                    asyncio.TimeoutError) as err:
                if attempts < max_soft_attempts:
                    logging.getLogger('bluetooth').warning(
                        'Could not command %s due to %s. Will Retry...',
                        addr, err)
                    # If a soft failure happens, that's okay, we'll simply
                    # retry again.
                    await soft_err_q.put((bot, attempts + 1))
                else:
                    logging.getLogger('bluetooth').error(
                        'Could not command %s after %d attempts. '
                        'Will re-attempt after hard reset.',
                        addr, max_soft_attempts)
                    # If a hard failure happens, however, we gotta push into
                    # the outer queue.
                    await hard_err_q.put(bot)

        bots_left: asyncio.Queue[Coachbot] = asyncio.Queue()
        for bot in bots:
            await bots_left.put(bot)

        hard_reset_attempt_i = 0
        while (
            hard_reset_attempt_i < hard_reset_attempts
            and not bots_left.empty()
        ):
            # For this hard attempt, copy all bots to the local queue.
            bot_queue: asyncio.Queue[Tuple[Coachbot, int]] = asyncio.Queue()
            while not bots_left.empty():
                await bot_queue.put((await bots_left.get(), 0))

            # Attempt to command all the bots.
            running_tasks: List[asyncio.Task] = []
            while not bot_queue.empty():
                bot, attempts = await bot_queue.get()

                # Parallel spawn all coachbot booting instructions using up as
                # many interfaces as available.
                running_tasks.append(
                    asyncio.create_task(boot_from_q(bot, attempts, bot_queue,
                                                    bots_left)))

            # Join on all tasks prior to exiting or reseting the bluetooth
            # service.
            await asyncio.wait(running_tasks)

            if not bots_left.empty():
                # We've had hard failures, let's restart the bluetooth service
                # in hopes that will fix it.
                logging.getLogger('bluetooth').error(
                    'A significant error happened. Bluetooth appears '
                    'unresponsive. Restarting the \'bluetooth\' service.')
                await (await create_subprocess_exec(
                    'systemctl', 'restart', 'bluetooth')).wait()
            else:
                logging.getLogger('bluetooth').debug(
                    'Successfully booted all required bots.')

            hard_reset_attempt_i += 1

        # If we still have bots left after this whole fiasco, that means that
        # even hard resetting didn't really fix anything
        while not bots_left.empty():
            yield BLENotReachableError(await bots_left.get())
