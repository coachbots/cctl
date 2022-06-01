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
        self.netstream_conf = configuration.video_stream
        self.input_stream = configuration.camera.raw_stream
        self.output_stream = configuration.camera.processed_stream
        self.ffmpeg_process: Optional[Process] = None
        self.stream_process: Optional[Process] = None
        self.hw_accel = configuration.camera.hardware_accel
        if self.hw_accel is None:
            logging.getLogger('camera').warning(
                'Hardware acceleration disabled. Check that '
                '/etc/coachswarm/cctld.conf has an overhead-camera/hwaccel '
                'field. Performance penalty induced. Continuing...')

    async def start_stream(self) -> None:
        """Starts the camera processing and upload stream."""
        await self.start_processing_stream()
        await self.start_net_stream()

    async def start_net_stream(self) -> None:
        """Starts the video processing and RTSP stream."""
        bitrate = self.netstream_conf.bitrate
        port = self.netstream_conf.rtsp_port
        codec = self.netstream_conf.codec
        command = [str(c) for c in [
            'cvlc', '-vvv'
            f'v4l2:/{self.output_stream}',
            '--sout',
            "'#"
                'transcode{'  # noqa: E131
                    f'codec={codec},vb={bitrate},acodec=none'  # noqa: E131
                '}'  # noqa: E131
                ':'  # noqa: E131
                'rtp{'  # noqa: E131
                    f'sdp=rtsp://:{port}/cctl/overhead'  # noqa: E131
                '}'  # noqa: E131
            "'"
        ]]
        logging.getLogger('camera').info('Starting RTSP stream: %s.',
                                         ' '.join(command))
        self.stream_process = await create_subprocess_exec(
            *command,
            stdin=DEVNULL, stdout=DEVNULL, stderr=PIPE)

    async def start_processing_stream(self) -> None:
        """Starts the video processing stream."""
        lenscorrection_filt = ':'.join([
            f'{key}={value}' for key, value in self.lens_correction.items()
        ])
        command = [str(c) for c in [
            'ffmpeg',
            *(['-hwaccel', self.hw_accel] if self.hw_accel is not None
              else []),
            '-loglevel', 'error', '-nostats', '-hide_banner',
            '-re', '-framerate', 30,
            '-i', self.input_stream,
            '-map', '0:v',
            '-vf', f'lenscorrection={lenscorrection_filt},format=yuv420p',
            '-f', 'v4l2', self.output_stream,
            '-async', 1, '-vsync', 1
        ]]
        logging.getLogger('camera').info('Starting processing stream: %s.',
                                         ' '.join(command))
        self.ffmpeg_process = await create_subprocess_exec(
            *command,
            stdin=DEVNULL, stdout=DEVNULL, stderr=PIPE)

    async def error_handler(self, process: Optional[Process],
                            error: Exception):
        """Called upon the camera processing stream failing."""
        if isinstance(error, RuntimeError):
            assert process is not None
            _, stderr = await process.communicate()
        else:
            stderr = b''

        logging.getLogger('camera').error('%s Stderr: %s', error, stderr)

    async def start_watchdog(self) -> None:
        """Runs a watchdog which ensures the camera stream is working."""
        async def on_end(process: Optional[Process], error: Exception):
            await self.error_handler(process, error)
            await self.kill_stream()

        while True:
            if self.ffmpeg_process is None:
                return await on_end(self.ffmpeg_process,
                                    ArgumentError('FFMpeg Process is None.'))
            if not await process_running(self.ffmpeg_process):
                return await on_end(self.ffmpeg_process,
                                    RuntimeError('FFMpeg Process Died.'))
            if self.stream_process is None:
                return await on_end(self.stream_process,
                                    ArgumentError('Stream Process is None.'))
            if not await process_running(self.stream_process):
                return await on_end(self.stream_process,
                                    RuntimeError('Stream Process Died.'))
            await asyncio.sleep(1)

    async def kill_stream(self) -> None:
        """Terminates the running stream."""
        for proc in (self.ffmpeg_process, self.stream_process):
            if proc is not None:
                proc.terminate()

    def __del__(self):
        asyncio.get_event_loop().run_until_complete(self.kill_stream())
