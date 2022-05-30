#!/usr/bin/env python

"""This exposes the BLE functions to CCTLD."""

from typing import Any, Callable, Coroutine, Iterable, AsyncGenerator, List, \
    Tuple
import asyncio
import copy
from dataclasses import dataclass, field
import logging
from uuid import UUID, uuid4

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


@dataclass
class BleInfo:
    """This dataclass contains the data that is required for BLE operation."""
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue())


BleRunnableT = Callable[..., Coroutine[Any, Any, Any]]


@dataclass
class BleTaskT:
    """Represents a BLE Task that is managed by the work queue."""
    runnable: BleRunnableT
    args: Tuple[Any, ...]
    uid: UUID

    async def run(self) -> Any:
        """Runs this task asynchronously. Returns a coroutine, in reality."""
        return await self.runnable(*self.args)


async def run(ble_info: BleInfo):
    """Runs the BLE server. This server will execute BLETaskT in the queue,
    forever.
    """
    while True:
        task = await ble_info.queue.get()
        await task.run()


async def add_task(ble_info: BleInfo, runnable: BleRunnableT, *args,
                   task_uuid=uuid4()) -> None:
    """Adds an additional task to the BLE server.

    Parameters:
        ble_info (BleInfo): The BleInfo AppState object.
        runnable (BleRunnableT): The function that represents a BLE-related
        task.
        *args: The arguments that will be passed to the function.
        task_uuid (UUID): The UUID of the task, if you wish to provide your
            own. If not passed, this function generates one on its own.

    Returns:
        UUID: A UUID identifying this task. This UUID allows you to
        differentiate between different tasks.
    """
    task = BleTaskT(runnable, args, task_uuid)
    logging.getLogger('bluetooth').debug('Adding task: %s.', task)
    await ble_info.queue.put(task)


async def run_tasks(ble_info: BleInfo,
                    args: List[Tuple[BleRunnableT, Tuple[Any, ...]]]):
    """Runs the specified task on the BLE server. This function is similar to
    the ``add_task`` function, however, unlike that function, this function
    waits for the tasks to be fully executed."""
    all_ids = [uuid4() for _ in args]
    remaining_uuids = copy.deepcopy(all_ids)
    results: List[Tuple[UUID, Any]] = []

    async def wrapper(fxn: BleRunnableT, uuid: UUID, *args: Tuple[Any, ...]):
        result = fxn(*args)
        del remaining_uuids[remaining_uuids.index(uuid)]
        results.append((uuid, result))

    for uuid, task in zip(all_ids, args):
        await add_task(ble_info, wrapper, task[0], uuid, task[1],
                       task_uuid=uuid)

    while len(remaining_uuids) > 0:
        await asyncio.sleep(300e-3)

    # TODO: Rewrite this algo a bit.
    # Supposed to sort results to match all_ids. Currently O(n^2) complexity.
    return [
        next(filter(lambda r: r[0] == u, results))[1]
        for u in all_ids
    ]


async def boot_bots(
    ble_info: BleInfo,
    bots: Iterable[Coachbot],
    state: bool
) -> AsyncGenerator[BLENotReachableError, None]:
    """Attempts to boot the given iterable MAC addresses up.

    Parameters:
        ble_info (BleInfo): The BleInfo of the AppState.
        bot_macs (Iterable[Coachbot]): The MAC addresses to attempt to boot up.
        state (bool): The state to attempt to boot to. If True, the bots turn
            on, otherwise they turn off.

    Returns:
        A generator of ``BLENotReachableError`` objects which can be used to
        figure out which robots could not be booted up.
    """
    max_attempts = 5

    async def runnable(bot: Coachbot):
        attempts = 0
        addr = bot.bluetooth_mac_address

        try:
            async with CoachbotBLEClient(addr, pair=True,
                                         timeout=10,) as client:
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
                # TODO: Request the same operation again.
            else:
                logging.getLogger('bluetooth').error(
                    'Could not command %s after %d attempts. Giving Up.',
                    addr, max_attempts)
                return BLENotReachableError(bot)

    results = await run_tasks(ble_info, [(runnable, (bot, )) for bot in bots])
    for result in results:
        yield result
