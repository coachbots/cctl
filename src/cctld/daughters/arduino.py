#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module exposes programming and control of the Arduino daughterboard.
Upon importing this module, it will check whether the Arduino needs any
updates, and automatically as required.
"""

import asyncio
import logging

from dataclasses import dataclass

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources
from serial import Serial
import cctl
from cctl.utils.asynctools import uses_lock
from cctl_static import arduino_daughter

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.0.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


@dataclass
class ArduinoInfo:
    """Encapsulates Arduino daughterboard data and functionality."""
    program_executable: str
    device_file: str
    baud_rate: int
    board_type: str
    conf_dir: str
    lock: asyncio.Lock = asyncio.Lock()

    async def __upload_arduino_script(self) -> None:
        """Uploads the static/arduino-daughter.ino script. Internal use only.
        This function automatically compiles it as required.
        """
        @uses_lock(self.lock)
        async def exec_operation(operation: str):
            flags = [
                '-b', self.board_type,
                '-p', self.device_file,
            ] + ([
                '--build-property',
                f'build.extra_flags="-DVERSION=\"{cctl.__version__}\""'
            ] if operation == 'compile' else [])

            with pkg_resources.path(arduino_daughter,
                                    'arduino_daughter.ino') as script_path:
                proc = await asyncio.create_subprocess_exec(
                    self.program_executable, operation, *flags,
                    str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)

                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    raise RuntimeError(
                        'Could not upload the Arduino script. '
                        'The error-code was %d and stderr: %r' %
                        (proc.returncode or 0, stderr))

                logging.debug('Successfully uploaded the Arduino script: %r.',
                              stdout.decode())

        await exec_operation('compile')
        await exec_operation('upload')

    async def update(self, force: bool) -> None:
        """Attempts to update the program on the arduino daughterboard.

        Parameters:
            force (bool): Whether to force update or not. If False, then this
            script will skip checking for version and simply force update the
            arduino daughterboard.

        Raises:
            SerialException: Upon a serial communication error.
        """
        if not force and await self.query_version() == cctl.__version__:
            return

        await self.__upload_arduino_script()

    async def query_version(self) -> str:
        """Queries the current version loaded on the arduino daughterboard.

        Returns:
            str: The version of the daughterboard.

        Raises:
            SerialException: Upon a serial communication error.
        """
        @uses_lock(self.lock)
        async def __helper() -> str:
            with Serial(self.device_file, self.baud_rate,
                        timeout=1) as ser:
                ser.write(b'V')  # Ask the Arduino to return the version.
                ser.reset_input_buffer()
                await asyncio.sleep(1e-1)
                # Last characters are \r\n. Trim those.
                return ser.readline().decode('ascii').rstrip()

        return await __helper()

    async def charge_rail_set(self, power: bool) -> None:
        """Changes the state of the charging rail

        Parameters:
            power (bool): Whether to set the power on or off.

        Raises:
            SerialException: Upon a serial communication error.
        """
        async def __helper():
            with Serial(self.device_file, self.baud_rate) as ser:
                ser.write(b'A' if power else b'D')
            await asyncio.sleep(10e-3)  # Relay delay is 10ms
        await __helper()
