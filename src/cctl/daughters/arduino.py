#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module exposes programming and control of the Arduino daughterboard."""

import asyncio
from typing import Union
import logging
from functools import wraps
try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources
from serial import Serial
import cctl
from cctl.api import configuration as config
from cctl.res import RES_STR
import static

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.5.1'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


ARDUINO_SCRIPT_PATH = pkg_resources.path(static, 'arduino-daughter')
ARDUINO_EXECUTABLE = config.get_arduino_executable_path()
PORT = config.get_arduino_daughterboard_port()
BAUD_RATE = config.get_arduino_daughterboard_baud_rate()
BOARD_TYPE = config.get_arduino_daughterboard_board()
ACCESS_LOCK = asyncio.Lock()


def __uses_lock(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        with (yield from ACCESS_LOCK):
            return function(*args, **kwargs)
    return wrapper


@__uses_lock
async def __upload_arduino_script() -> None:
    """Uploads the static/arduino-daughter.ino script. Internal use only. This
    function automatically compiles it as required.
    """
    async def exec_operation(operation: str) -> int:
        flags = [
            f'--fqbn {BOARD_TYPE}',
            f'-p {PORT}',
            '--build-property ' +
            f'"build.extra_flags=\"-DVERSION={cctl.__VERSION__}\""'
        ] if operation == 'compile' else [
            f'--fqbn {BOARD_TYPE}',
            f'-p {PORT}',
        ]
        proc = await asyncio.create_subprocess_shell(' '.join([
            ARDUINO_EXECUTABLE, operation, *flags, str(ARDUINO_SCRIPT_PATH)
        ]), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logging.error(RES_STR['logging']['arduino_upload_err'],
                          proc.returncode, stderr)
            return -1

        logging.debug(RES_STR['logging']['arduino_upload_success'], stdout)
        return 0

    if exec_operation('compile') == 0:
        exec_operation('upload')


@__uses_lock
async def query_version() -> str:
    """Queries the current version loaded on the arduino daughterboard.

    Returns:
        str: The version of the daughterboard.
    """
    with Serial(PORT, BAUD_RATE, timeout=3.0) as ser:
        ser.write(b'V')  # Ask for the daughterboard to return the version.
        return ser.readline()[:1]  # Remove the last newline character.


async def update(force: bool = False) -> None:
    """Attempts to update the program on the arduino daughterboard.

    Parameters:
        force (bool): Whether to force update or not. If False, then this
        script will skip checking for version and simply force update the
        arduino daughterboard.
    """
    if not force and await query_version() == cctl.__VERSION__:
        return

    await __upload_arduino_script()


@__uses_lock
async def charge_rail_set(power: bool) -> None:
    """Changes the state of the charging rail

    Parameters:
        power (bool): Whether to set the power on or off.
    """
    with Serial(PORT, BAUD_RATE) as ser:
        ser.write(b'A' if power else b'D')
