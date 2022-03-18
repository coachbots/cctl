# -*- coding: utf-8 -*-

"""
This module exposes various functions for controlling robots.
"""

from contextlib import contextmanager
from typing import Callable, Generator, Iterable, Tuple, Union, List
from subprocess import DEVNULL, call
import asyncio
import os
from os import path
import shutil
import time
import logging
import socket

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

import paramiko
from paramiko.channel import ChannelFile
from cctl import netutils

from cctl.api import configuration
from cctl.res import RES_STR
from cctl.netutils import async_host_is_reachable, get_broadcast_address, \
    get_ip_address, read_remote_file, ssh_client
import static


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
        return self.identifier == other.identifier

    def __lt__(self, other: 'Coachbot') -> bool:
        return self.identifier < other.identifier

    def __le__(self, other: 'Coachbot') -> bool:
        return self.identifier <= other.identifier

    def __gt__(self, other: 'Coachbot') -> bool:
        return self.identifier > other.identifier

    def __ge__(self, other: 'Coachbot') -> bool:
        return self.identifier >= other.identifier

    def __ne__(self, other: 'Coachbot') -> bool:
        return self.identifier != other.identifier

    def __str__(self) -> str:
        return f'Coachbot({self.identifier})'

    def __repr__(self) -> str:
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

    @property
    def mac_address(self) -> str:
        """Returns the MAC address of self."""
        # TODO: Not sure if pkg_resources caches or not, this could be costly.
        file = pkg_resources.read_text(static, 'mac_addresses').split('\n')
        return file[self.identifier - 1]

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
        MAX_ATTEMPTS = 4

        count = 0
        while not await self.async_is_alive() or count < MAX_ATTEMPTS:
            process = await asyncio.create_subprocess_exec(
                './ble_one.py',
                str(int(state)),
                str(self.identifier),
                cwd=configuration.get_server_dir(),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait([process.wait()], timeout=10)
            try:
                process.terminate()
                logging.debug(RES_STR['state_change_retry'], self.identifier)
            except ProcessLookupError:
                # The process finished successfully, we can leave this fxn.
                return
            count += 1

        logging.error(RES_STR['state_change_max_attempts'], self.identifier)

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

    async def async_blink(self) -> None:
        """Asynchronously blinks the robot.

        .. warning:: I am lying -- this is not asynchronous as of now. It's 1AM
            and I just want it to work.

        Note:
            There's much we can reverse-engineer from this function. The bots
            are running something on port 5005 which is listening. The
            broadcast IP address ensures that anything on the network receives
            this packet. Now, 192.168.1.2 is not listening on 5005. You can
            check that with:

            .. code-block:: bash

               sudo lsof -iTCP -sTCP:LISTEN -P -n

            That means that all the coach-os' are listening on 5005. However,
            dangerously, led_blink doesn't attempt to target a specific bot,
            rather broadcasting its request to all robots where the parameter
            is the id.

        Todo:
            Clean up this function, I merely reimplemented it as it was
            (without the ifconfig parsing).
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        br_addr = get_broadcast_address(configuration.get_server_interface())
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            for _ in range(200):
                await asyncio.sleep(0.05)
                sock.sendto(bytes(f'LED_ON|{self.identifier}', 'ascii'),
                            (br_addr, 5005))
        finally:
            sock.close()

    async def async_fetch_legacy_log(self):
        """This function is an implementation of the legacy behavior for
        copying legacy ``experiment_log`` logs into an output directory.

        Warning:
            This function does not check if targets are online. Make sure you
            are not attempting to copy from a target that is not online.

        Returns:
            bytes: The contents of the remote file path.
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, read_remote_file, self.address,
            configuration.get_legacy_log_file_path())

    def fetch_legacy_log(self):
        """This function is an implementation of the legacy behavior for
        copying legacy ``experiment_log`` logs into an output directory.

        Returns:
            bytes: The contents of the remote file path.

        Example:

        .. code-block:: python

           m_log = bot.fetch_legacy_log()
           with open(f'my_log_dir/{bot.identifier}', 'wb') as f:
               f.write(m_log)

        Warning:
            This function does not check if targets are online. Make sure you
            are not attempting to copy from a target that is not online.

        Raises:
            FileNotFoundError: If the experiment_log does not exist.
        """
        return asyncio.get_event_loop().run_until_complete(
            self.async_fetch_legacy_log())

    async def async_upload_user_code(self,
            path_to_usr_code: str, os_update: bool,
            path_to_os: str = path.join(configuration.get_server_dir(),
                                        'temp')) -> bool:
        """Asynchronously uploads code to the specified Coachbot if it is
        alive.

        Checks whether the coachbot is online.

        Parameters:
            path_to_usr_code (str): The path to the user code to upload.
            os_update (bool): Flag indicating whether an os update should be
                performed.

        Returns:
            bool: Whether the Coachbot was updated.
        """
        if not self.is_alive():
            return False

        remote_path = configuration.get_coachswarm_remote_path()

        if os_update:
            try:
                # TODO: Not really async
                with netutils.sftp_client(self.address) as sftp:
                    for file in sftp.listdir(remote_path):
                        sftp.remove(path.join(remote_path, file))
                    for file in os.listdir(path_to_os):
                        sftp.put(path.join(path_to_os, file),
                                 path.join(remote_path, file))
            except paramiko.SFTPError as sftp_err:
                logging.error(sftp_err)

            await self.async_boot(False)
            await self.async_boot(True)

        # Not really async.
        with open(path_to_usr_code, 'rb') as usr_code:
            netutils.write_remote_file(
                self.address, configuration.get_coachswarm_remote_path(),
                usr_code.read())

        return True

    @contextmanager
    def run_ssh(self, command: str,
                back_proxy: int) -> Generator[Tuple[ChannelFile, ChannelFile,
                                                    ChannelFile], None, None]:
        """Runs a command over ssh. This command invokes a shell.

        Parameters:
            command (str): The command to execute on the Coachbot.
            back_proxy (int): A flag that controls whether the Coachbot should
                be connected back to cctl. If this flag is set to a non-zero
                number, then the Coachbot will open up a SOCKS5 proxy back to
                the machine running cctl. The number given is the port the
                machine will open its proxy to. This flag is useful when you
                want to execute a command that requires internet access.

        Raises:
            SSHError: If an error is thrown during command execution.
        """
        with ssh_client(self.address) as client:
            should_proxy = back_proxy > 0
            try:
                if should_proxy:
                    interface = configuration.get_server_interface()
                    proxy_user = configuration.get_socks5_proxy_user()

                    _, stdout, _ = client.exec_command(
                        f'sh -c "ssh -D {back_proxy} -f -C -q -N ' +
                        f'-i ~/.ssh/id_{proxy_user} ' +
                        f'{proxy_user}@{get_ip_address(interface)} ' +
                        '& echo $!"')
                    stdout.channel.recv_exit_status()
                yield client.exec_command(command)
            finally:
                if should_proxy is not None:
                    # TODO: Change this nonsense command
                    _, stdout, _ = client.exec_command('pkill -15 ssh')
                    stdout.channel.recv_exit_status()


def get_all_coachbots() -> List[Coachbot]:
    """Returns a list of all Coachbots."""
    return [Coachbot(i) for i in configuration.get_valid_coachbot_range()]


async def async_get_alives(bots: Iterable[Coachbot]) \
        -> List[Coachbot]:
    """Asynchronously returns a generator of bots that are active.

    Parameters:
        bs (Iterable[Coachbot]): The set of bots to check if they are alive.

    Returns:
        List[Coachbot]: The list of alive bots.

    Warning:
        This function may not return bots in the same order as what you
        inputted.

    Todo:
        Mildly dirty implementation.
    """
    async def _helper(bot: Coachbot, result_l: List[Coachbot]):
        if await bot.async_is_alive():
            result_l.append(bot)

    m_list = []
    await asyncio.gather(*(_helper(bot, m_list) for bot in bots))
    return m_list


def get_alives(
        bots: Iterable[Coachbot] = (Coachbot(i) for i in range(0, 100))) \
        -> List[Coachbot]:
    """Returns a generator of bots that are active.

    Parameters:
        bs (Iterable[Coachbot]): The set of bots to check if they are alive.

    Returns:
        List[Coachbot]: The list of alive bots.

    Warning:
        This function may not return bots in the same order as what you
        inputted.
    """
    async def _helper():
        return await async_get_alives(bots)

    return asyncio.get_event_loop().run_until_complete(_helper())


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

    tasks = [asyncio.get_event_loop().create_task(bot.async_boot(state))
             for bot, state in zip(bots, state_l)]

    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))


def blink_bots(bots: Union[Iterable[Coachbot], str]):
    """Blinks a plethora of bots.

    Todo:
        Broken

    Parameters:
        bots (Iterable[Coachbot] | str): The list of bots. This list can
            contain either Coachbots or a string 'all'. If this list contains
            both, then the algorithm only boots all bots, once.
    """
    m_bots = get_all_coachbots() if isinstance(bots, str) else bots
    asyncio.get_event_loop().run_until_complete(
        asyncio.wait([asyncio.get_event_loop().create_task(bot.async_blink())
                      for bot in m_bots]))


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


async def async_upload_codes(path_to_usr_code: str, os_update: bool,
                             targets: Union[List[Coachbot], str]) -> None:
    """Uploads user code and possibly OS code in an asynchronous manner to the
    specified targets.

    Parameters:
        path_to_usr_code (str): The path to the user code to upload.
        os_update (bool): Flag indicating whether an os update should be
            performed.
        targets (Iterable[Coachbot] | str): The targets to upload to. If this
            is a string, then the function uploads to all online bots.
    """

    m_targets = targets if isinstance(targets, List) \
        else await async_get_alives(get_all_coachbots())

    asyncio.gather(bot.async_upload_user_code(path_to_usr_code, os_update)
                   for bot in m_targets)


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
                          states: Union[bool, Iterable[bool]]) -> None:
    """Blocks execution until all bots meet the specified state.

    Example:

    .. code-block:

       # Wait until bots 1 and 2 are on and 3 is off.
       wait_until_bots_state([1, 2, 3], [True, True, False])

       # Wait until 3, 4, 5 are all on.
       wait_until_bots_state([3, 4, 5], 3 * [True])

    Parameters:
        bots (Iterable[Coachbot]): The bots to test.
        states (bool | Iterable[bool]): The states that those bots need tomeet.
    """
    m_states = (True for _ in bots) if isinstance(states, bool) else states

    async def _internal():
        asyncio.gather(bot.async_wait_until_state(state)
                       for bot, state in zip(bots, m_states))

    asyncio.get_event_loop().run_until_complete(_internal())


async def async_fetch_legacy_logs(
        bots: Iterable[Coachbot],
        on_fetch: Callable[[Coachbot, bytes], None] = lambda *_: None) \
        -> Tuple[bytes]:
    """Asynchronously fetches legacy logs.

    Parameters:
        bots (Iterable[Coachbot]): The bots of which to fetch the logs.
        on_fetch (Callable[[Coachbot, bytes], None]): Callable called when a
            log is fetched. Note that this callable is called for each fetched
            log, which enables much faster execution.

    Returns:
        Tuple[bytes]: The logs in the same order as bots.

    Raises:
        FileNotFoundError: If the experiment_log does not exist.
    """
    async def _helper(bot: Coachbot) -> bytes:
        logs = await bot.async_fetch_legacy_log()
        on_fetch(bot, logs)
        return logs

    return await asyncio.gather(*(_helper(bot) for bot in bots))


def fetch_legacy_logs(
        bots: Iterable[Coachbot],
        on_fetch: Callable[[Coachbot, bytes], None] = lambda *_: None) \
        -> Tuple[bytes]:
    """Synchronously fetches legacy logs.

    Parameters:
        bots (Iterable[Coachbot]): The bots of which to fetch the logs.
        on_fetch (Callable[[Coachbot, bytes], None]): Callable called when a
            log is fetched. Note that this callable is called for each fetched
            log, which enables much faster execution.

    Warning:
        If you decide to use ``on_fetch`` make sure you use the Coachbot
        parameter for testing for a target bot. For example:

        .. code-block:: python

           # This is invalid
           counter = 4
           def my_on_fetch_handler(bot, log_data):
               nonlocal counter
               with open('my_file.txt', 'w+b') as m_file:
                   m_file.write(log_data)
                   if counter == 4:
                       m_file.write('Some more data for bot 4'.encode('utf-8'))

           # This is valid
           def my_on_fetch_handler(bot, log_data):
               with open('my_file.txt', 'w+b') as m_file:
                   m_file.write(log_data)
                   if bot.identifier == 4:
                       m_file.write('Some more data for bot 4'.encode('utf-8'))

    Returns:
        Tuple[bytes]: The logs in the same order as bots.

    Raises:
        FileNotFoundError: If the experiment_log does not exist.
    """
    return asyncio.get_event_loop().run_until_complete(
        async_fetch_legacy_logs(bots, on_fetch))
