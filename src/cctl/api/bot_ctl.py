# -*- coding: utf-8 -*-

"""
This module exposes various functions for controlling robots.
"""

from typing import List, Union
from subprocess import call
import os
import shutil
import time
import logging

from cctl.api import configuration
from cctl.res import RES_STR


def boot_bot(bot_id: Union[str, int], state: bool) -> None:
    """
    Changes the state of a bot to on or off.

    Parameters:
        bot_id: Target bot. If this parameter is a string 'all', then all
            robots are turned on/off. All other string values raise errors.
        state: Whether to boot on or off

    Raises:
        ValueError: Raised when a string not-equal-to 'all' is passed.

    Todo:
        Currently, this function calls an extrenal script. It should, rather,
        be invoking it as a function from the module.
    """
    # Handle the case of all bots.
    if isinstance(bot_id, str) and bot_id == 'all':
        if state:
            call(['./reliable_ble_on.py'], cwd=configuration.get_server_dir())
            return
        call(['./reliable_ble_off.py'], cwd=configuration.get_server_dir())
        return

    if isinstance(bot_id, str):
        raise ValueError(RES_STR['invalid_bot_id_exception'])

    call(['./ble_one.py', str(int(state)), str(bot_id)],
         cwd=configuration.get_server_dir())


def boot_bots(bots: Union[List[Union[str, int]], str],
              states: Union[bool, List[bool]]) -> None:
    """
    Changes the state of a plethora of bots on or off.

    Parameters:
        bots: The list of bots. This list can contain either integers
            (representing bot IDs) or a string 'all'. If this list contains
            both, then the algorithm only boots all bots, once.
        state: The list of states for all bots. This string should have the
            exact same number of elements as ``bots``. It can also be a boolean
            which controls the state of all bots.

    Raises:
        ValueError: Raised when a string not-equal-to 'all' is passed.

    Todo:
        Currently, this function calls an extrenal script. It should, rather,
        be invoking it as a function from the module.
    """
    if isinstance(bots, str) and bots == 'all':
        if not isinstance(states, bool):
            raise ValueError(RES_STR['invalid_bot_id_exception'])
        boot_bot('all', True)
        return

    if isinstance(bots, str):
        raise ValueError(RES_STR['invalid_bot_id_exception'])

    state_l = states if isinstance(states, List) else [states] * len(bots)

    if 'all' in bots:
        boot_bot('all', state_l[bots.index('all')])
        return

    for bot, state in zip(bots, state_l):
        boot_bot(bot, state)


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
