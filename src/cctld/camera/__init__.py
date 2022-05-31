"""This module exposes functions for controlling camera source and sink."""

import asyncio
from ctypes import ArgumentError
import logging
from asyncio.subprocess import create_subprocess_exec, Process, DEVNULL
from subprocess import PIPE
from typing import Optional
from cctld.utils.asyncio import process_running
from cctld.conf import Config


class ProcessingStream:
    """Controls the ProcessingStream. This is to be used as an async context
    manager."""
    def __init__(self, configuration: Config) -> None:
        self.lens_correction = {
            'k1': configuration.camera.lens_k1,
            'k2': configuration.camera.lens_k2,
            'cx': configuration.camera.lens_cx,
            'cy': configuration.camera.lens_cy
        }
        self.input_stream = configuration.camera.raw_stream
        self.output_stream = configuration.camera.processed_stream
        self.running_process: Optional[Process] = None

    async def start_stream(self) -> None:
        """Starts the video stream."""
        lenscorrection_filt = ':'.join([
            f'{key}={value}' for key, value in self.lens_correction.items()
        ])
        command = [
            'ffmpeg', '-re', '-i', self.input_stream,
            '-map', '0:v',
            '-vf', f'lenscorrection={lenscorrection_filt},format=yuv420p',
            '-f v4l2', self.output_stream
        ]
        logging.getLogger('camera').info('Starting processing stream: %s.',
                                         ' '.join(command))
        self.running_process = await create_subprocess_exec(
            *command,
            stdin=DEVNULL, stdout=DEVNULL, stderr=PIPE)

    async def error_handler(self, error: Exception):
        """Called upon the camera processing stream failing."""
        if isinstance(error, RuntimeError):
            assert self.running_process is not None
            _, stderr = await self.running_process.communicate()
        else:
            stderr = b''

        logging.getLogger('camera').error('%s Stderr: %s', error, stderr)

    async def start_watchdog(self) -> None:
        """Runs a watchdog which ensures the camera stream is working."""
        while True:
            if self.running_process is None:
                await self.error_handler(
                    ArgumentError('Running Process is None.'))
            elif not process_running(self.running_process):
                await self.error_handler(
                    RuntimeError('Running Process Died.'))
            return

    async def kill_stream(self) -> None:
        """Terminates the running stream."""
        if self.running_process is None:
            return
        self.running_process.terminate()

    def __del__(self):
        asyncio.get_event_loop().run_until_complete(self.kill_stream())
