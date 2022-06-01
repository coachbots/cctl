#!/usr/bin/env python

"""This module exposes the configuration used for cctld."""

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.0.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

from configparser import ConfigParser, NoOptionError
import logging
import sys
from typing import List, Optional

from cctld.res import ExitCode


CONF_PATH = '/etc/coachswarm/cctld.conf'

config = ConfigParser()

if len(config.read(CONF_PATH)) == 0:
    logging.error('Could not read %s. Please ensure it exists.', CONF_PATH)
    sys.exit(ExitCode.EX_CONFIG)


# TODO: Should check for validity of the file before using it.

class Config:
    """The configuration properties."""

    class General:
        """Returns the confvals under the ``general`` header."""
        @property
        def workdir(self) -> str:
            """Returns the working directory of cctld."""
            return config.get('general', 'workdir')

    class CoachClient:
        """Returns the configurations under the ``coach_client`` header."""

        @property
        def command_port(self) -> int:
            """Returns the port on which the coachbots are listening for
            commands."""
            return config.getint('coach_client', 'command_port')


    class CoachServers:
        """Returns the configurations under the ``coach_servers``header."""

        @property
        def status_host(self) -> str:
            """Returns the host/port which will listen for Coachbot statues."""
            return config.get('coach_servers', 'status_host')

    class IPC:
        """Returns the configs under the ``api`` header."""
        @property
        def request_feed(self) -> str:
            """Returns the full path of the IPC request file."""
            return config.get('api', 'request_feed')

        @property
        def state_feed(self) -> str:
            """Returns the full path to the coachbot state feed file."""
            return config.get('api', 'state_feed')

        @property
        def signal_feed(self) -> str:
            """Returns the path to which cctl APIs can bind to listen for
            signals."""
            return config.get('api', 'signal_feed')

    class Bluetooth:
        """Returns all the information under the ``bluetooth`` header."""

        @property
        def interfaces(self) -> List[int]:
            """Returns the list of interfaces that are available for BT
            consumption."""
            return [int(i) for i in
                    config.get('bluetooth', 'interfaces').split(',')]

    class Arduino:
        """Returns all the information under the ``arduino`` header."""

        @property
        def executable(self) -> str:
            """Returns the full path to the Arduino executable."""
            return config.get('arduino', 'executable_path')

        @property
        def serial(self) -> str:
            """Returns the full path on which the arduino is mounted."""
            return config.get('arduino', 'serial')

        @property
        def baud_rate(self) -> int:
            """Returns the Arduino daughterboard baud rate."""
            return config.getint('arduino', 'baudrate')

        @property
        def board_type(self) -> str:
            """Returns the board type of the Arduino."""
            return config.get('arduino', 'board')

    class VideoStream:
        """This class exposes video-related configuration points."""
        @property
        def bitrate(self) -> int:
            """Returns the video stream bitrate in kbps"""
            return config.getint('video-stream', 'bitrate')

        @property
        def rtsp_host(self) -> str:
            """Returns the host on which the RTSP stream will be played."""
            return config.get('video-stream', 'rtsp_host')

        @property
        def codec(self) -> str:
            """Returns the codec used for transcoding."""
            return config.get('video-stream', 'codec')

    class Camera:
        @property
        def lens_k1(self) -> float:
            """Returns the k1 correction factor."""
            return config.getfloat('overhead-camera', 'lens_k1')

        @property
        def lens_k2(self) -> float:
            """Returns the k2 correction factor."""
            return config.getfloat('overhead-camera', 'lens_k2')

        @property
        def lens_cx(self) -> float:
            """Returns the cx correction factor."""
            return config.getfloat('overhead-camera', 'lens_cx')

        @property
        def lens_cy(self) -> float:
            """Returns the cy correction factor."""
            return config.getfloat('overhead-camera', 'lens_cy')

        @property
        def raw_stream(self) -> str:
            """Returns the path of the raw stream."""
            return config.get('overhead-camera', 'raw_stream')

        @property
        def processed_stream(self) -> str:
            """Returns the path of the processed stream."""
            return config.get('overhead-camera', 'processed_stream')

        @property
        def hardware_accel(self) -> Optional[str]:
            """Returns a string that determines which hardware acceleration
            will be used. Returns None if no hardware acceleration is defined.
            """
            try:
                return config.get('overhead-camera', 'hwaccel')
            except NoOptionError:
                return None

    @property
    def general(self) -> 'Config.General':
        return Config.General()

    @property
    def bluetooth(self) -> 'Config.Bluetooth':
        return Config.Bluetooth()

    @property
    def servers(self) -> 'Config.CoachServers':
        return Config.CoachServers()

    @property
    def ipc(self) -> 'Config.IPC':
        return Config.IPC()

    @property
    def coach_client(self) -> 'Config.CoachClient':
        return Config.CoachClient()

    @property
    def arduino(self) -> 'Config.Arduino':
        return Config.Arduino()

    @property
    def camera(self) -> 'Config.Camera':
        return Config.Camera()

    @property
    def video_stream(self) -> 'Config.VideoStream':
        return Config.VideoStream()
