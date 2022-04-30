#!/usr/bin/env python

"""This module exposes the configuration used for cctld."""

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

from configparser import ConfigParser
import logging
import sys

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

    class CoachServers:
        """Returns the configurations under the ``coach_servers``header."""
        @property
        def status_port(self) -> int:
            """Returns the port of the status server."""
            return config.getint('coach_servers', 'status_port')

        @property
        def interface(self) -> str:
            """Returns the default interface to be used for communicating with
            the Coachbots."""
            return config.get('coach_servers', 'interface')

    class IPC:
        """Returns the configs under the ``ipc`` header."""
        @property
        def request_feed(self) -> str:
            """Returns the full path of the IPC request file."""
            return config.get('ipc', 'request_feed')

        @property
        def state_feed(self) -> str:
            """Returns the full path to the coachbot state feed file."""
            return config.get('ipc', 'state_feed')

    @property
    def general(self) -> 'Config.General':
        return Config.General()

    @property
    def servers(self) -> 'Config.CoachServers':
        return Config.CoachServers()

    @property
    def ipc(self) -> 'Config.IPC':
        return Config.IPC()
