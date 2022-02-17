# -*- coding: utf-8 -*-

"""
This module exposes various functions for controlling robots.
"""

from typing import Generator, Iterable, Union
from subprocess import DEVNULL, call
import asyncio
import os
import shutil
import time
import logging

from cctl.api import configuration
from cctl.res import RES_STR
from cctl.netutils import async_host_is_reachable


class Coachbot:
    """Class representing a Coachbot. Use this class for Coachbot
    operations.
    """

    IP_ADDRESS_SHIFT = 3

    def __init__(self, identifier: int) -> None:
        """Constructs a Coachbot.

        Raises:
            ValueError: If the identifier does not fit the configured Coachbot
                range.
        """
        if identifier not in configuration.get_valid_coachbot_range():
            raise ValueError

        self.identifier = identifier

    def __eq__(self, other: 'Coachbot') -> bool:
        """Tests for equality based on the identifier of the Coachbot.

        Returns:
            bool: Whether the objects are equal.
        """
        return self.identifier == other.identifier

    def __str__(self) -> str:
        """Converts the Coachbot to a string.

        Returns:
            str: The string representation of the Coachbot
        """
        return f'Coachbot({self.identifier})'

    def __repr__(self) -> str:
        """Converts the Coachbot as a string.

        Returns:
            str: The string representation of the Coachbot
        """
        return f'Coachbot<id={self.identifier}>'

    @property
    def address(self) -> str:
        """Returns the IP address of self.

        Returns:
            str: The correct hostname of self.
        """
        return f'192.168.1.{self.identifier + Coachbot.IP_ADDRESS_SHIFT}'

    async def async_is_alive(self) -> bool:
        """Asynchronously checks whether self is booted and accessible.

        Returns:
            bool: Whether self is on.
        """
        return await async_host_is_reachable(self.address)

    async def async_wait_until_state(self, state: bool,
                                     sleep_time: float = 3) -> None:
        """Asynchronously waits until self is alive and reachable over network,
        or not, depending on the state parameter.

        Parameters:
            state (bool): The target state to meet.
            sleep_time (float): The number of seconds to sleep between polls.
        """
        while not await self.async_is_alive() == state:
            await asyncio.sleep(sleep_time)

    def wait_until_state(self, state: bool) -> None:
        """Blocks execution until self is alive and reachable or not, depending
        on the parameter.

        Parameters:
            state (bool): The target state
        """
        asyncio.get_event_loop().run_until_complete(
            self.async_wait_until_state(state))

    def is_alive(self) -> bool:
        """Checks whether self is booted and accessible.

        Returns:
            bool: Whether self is on.

        Note:
            This function may possibly be slow due to the fact that it has to
            ping the coachbot over network.
        """
        return asyncio.get_event_loop().run_until_complete(
            self.async_is_alive())

    @staticmethod
    def from_address(address: str) -> 'Coachbot':
        """Builds a Coachbot from the given ip address.

        Properties:
            address (str): The target ip address.

        Returns:
            Coachbot: The bot corresponding to the given IP address.
        """
        return Coachbot(int(address.split('.')[-1]) -
                        Coachbot.IP_ADDRESS_SHIFT)

    async def async_boot(self, state: bool) -> None:
        """
        Asynchronously changes the state of a bot to on or off.

        Contrary to legacy implementation, this function pauses execution until
        the bot is fully reachable.

        Parameters:
            state (bool): Whether to boot on or off

        Example:

        .. code-block:

           # This code will attempt to boot bots 90-95 in a very faster manner
           # (spawning 6 boot-up functions) but will block until all robots are
           # done.
           # Note that this needs to be in an async function.
           m_bots = (Coachbot(i) for i in range(90, 95))
           asyncio.gather(*(async_boot_bot(bot, True) for bot in m_bots))

        Raises:
            ValueError: Raised when a string not-equal-to 'all' is passed.

        Todo:
            Currently, this function calls an extrenal script. It should,
            rather, be invoking it as a function from the module.
        """
        await asyncio.create_subprocess_exec(
            './ble_one.py',
            str(int(state)),
            str(self.identifier),
            cwd=configuration.get_server_dir(),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        await self.async_wait_until_state(state)

    def boot(self, state: bool) -> None:
        """
        Synchronously changes the state of a bot to on or off.

        Contrary to legacy implementation, this function pauses execution until
        the bot is fully reachable.

        Parameters:
            state (bool): Whether to boot on or off

        Raises:
            ValueError: Raised when a string not-equal-to 'all' is passed.
        """
        asyncio.get_event_loop().run_until_complete(self.async_boot(state))


async def async_get_alives(bots: Iterable[Coachbot]) \
        -> Generator[Coachbot, None, None]:
    """Asynchronously returns a generator of bots that are active.

    Parameters:
        bs (Iterable[Coachbot]): The set of bots to check if they are alive.

    Returns:
        Generator: A generator yielding Coachbot objects only if they are
        active.

    Note:
        This function may potentially be slow because it has to ping each bot.
        The implementation is a cleaned-up implementation of legacy behavior.
    """
    tasks = [asyncio.ensure_future(bot.async_is_alive()) for bot in bots]
    await asyncio.wait(tasks)
    return (bot for bot, task in zip(bots, tasks) if task.result())


def get_alives(
        bots: Iterable[Coachbot] = (Coachbot(i) for i in range(0, 100))) \
        -> Generator[Coachbot, None, None]:
    """Returns a generator of bots that are active.

    Parameters:
        bs (Iterable[Coachbot]): The set of bots to check if they are alive.

    Returns:
        Generator: A generator yielding Coachbot objects only if they are
        active.

    Note:
        This function may potentially be slow because it has to ping each bot.
        The implementation is a cleaned-up implementation of legacy behavior.
    """
    return asyncio.get_event_loop().run_until_complete(async_get_alives(bots))


def boot_bots(bots: Union[Iterable[Coachbot], str],
              states: Union[bool, Iterable[bool]]) -> None:
    """
    Changes the state of a plethora of bots on or off.

    Parameters:
        bots (Iterable[Coachbot] | str): The list of bots. This list can
            contain either Coachbots or a string 'all'. If this list contains
            both, then the algorithm only boots all bots, once.
        state (Iterable[bool] | bool): The list of states for all bots. This
            string should have the exact same number of elements as ``bots``.
            It can also be a boolean which controls the state of all bots.

    Raises:
        ValueError: Raised when a string not-equal-to 'all' is passed.

    Todo:
        * Currently, this function calls an extrenal script. It should, rather,
        be invoking it as a function from the module.
    """
    async def _internal():
        def _boot_all(state: bool) -> None:
            call(
                f'./reliable_ble_{"on" if state else "off"}.py',
                cwd=configuration.get_server_dir(),
                stdout=DEVNULL,
                stderr=DEVNULL)

        if isinstance(bots, str) and bots == 'all':
            if not isinstance(states, bool):
                raise ValueError(RES_STR['invalid_bot_id_exception'])

            _boot_all(states)
            return

        if isinstance(bots, str):
            raise ValueError(RES_STR['invalid_bot_id_exception'])

        state_l = states if isinstance(states, Iterable) \
            else (states for _ in bots)

        asyncio.gather(
            *(bot.async_boot(state) for bot, state in zip(bots, state_l)))

    asyncio.get_event_loop().run_until_complete(_internal())


def set_user_code_running(state: bool) -> None:
    """
    Turns user code on robots on or off.

    Parameters:
        state: Whether to unpause or pause

    Todo:
        Currently, this function calls an extrenal script. It should, rather,
        be invoking it as a function from the module.
    """
    if state:
        call(['./start.py'], cwd=configuration.get_server_dir())
        return

    call(['./stop.py'], cwd=configuration.get_server_dir())


def blink(robot_id: Union[int, str]) -> None:
    """
    Blinks a robot.

    Parameters:
        bot_id: Target bot. If this is a string with the value 'all', then all
            robots are blinked. All other strings raise ValueError

    Raises:
        ValueError: Raised when a string not-equal-to 'all' is passed.

    Todo:
        Shouldn't be implemented the way it is. Should be calling a module
        function.
    """
    def _blink_internal(i: int) -> None:
        call(['./led_on.py', str(i)], cwd=configuration.get_server_dir())

    if isinstance(robot_id, str) and robot_id == 'all':
        for i in range(0, 100):
            _blink_internal(i)
        return

    if isinstance(robot_id, str):
        raise ValueError(RES_STR['invalid_bot_id_exception'])

    _blink_internal(robot_id)


def upload_code(path_to_usr_code: str, os_update: bool) -> None:
    """
    Uploads user code to all robots.

    Parameters:
        path_to_usr_code: The path to the target user code.
        os_update: Whether the operating system should be reinstalled.

    Note:
        This function overwrites the `usr_code.py` in
        ``$SERVERDIR/temp/usr_code.py``.

    Todo:
        Currently, this function calls an extrenal script. It should, rather,
        be invoking it as a function from the module.
    """
    server_tmp = os.path.join(configuration.get_server_dir(), 'temp')

    shutil.copy2(path_to_usr_code, os.path.join(server_tmp, 'usr_code.py'))

    if not os_update:
        logging.info(RES_STR['upload_msg'])
        call(['./update.py', configuration.get_server_interface()],
             cwd=configuration.get_server_dir())
        return

    logging.info(RES_STR['upload_os_msg'])
    shutil.copy2(configuration.get_coachswarm_conf_path(),
                 os.path.join(server_tmp, 'coachswarm.conf'))
    # TODO: Remove these sleeps with a while loop.
    # TODO: I don't really know what this code does.
    call(['./scan.py'], cwd=configuration.get_server_dir())
    time.sleep(0.5)
    call(['./hard_push.py', configuration.get_server_interface()],
         cwd=configuration.get_server_dir())
    time.sleep(0.5)
    call(['./reboot_batch.py', configuration.get_server_interface()],
         cwd=configuration.get_server_dir())


def wait_until_bots_state(bots: Iterable[Coachbot],
                          states: Iterable[bool]) -> None:
    """Blocks execution until all bots meet the specified state.

    Example:

    .. code-block:

       # Wait until bots 1 and 2 are on and 3 is off.
       wait_until_bots_state([1, 2, 3], [True, True, False])

       # Wait until 3, 4, 5 are all on.
       wait_until_bots_state([3, 4, 5], 3 * [True])

    Parameters:
        bots (Iterable[Coachbot]): The bots to test.
        states (Iterable[bool]): The states that those bots need to meet.
    """
    async def _internal():
        asyncio.gather(bot.async_wait_until_state(state)
                       for bot, state in zip(bots, states))
    asyncio.get_event_loop().run_until_complete(_internal())
