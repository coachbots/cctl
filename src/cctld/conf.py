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

from configparser import ConfigParser
import logging
import sys
from typing import List

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
