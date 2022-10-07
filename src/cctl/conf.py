#!/usr/bin/env python

"""This module exposes the configuration cctl uses."""

import os
import logging
import sys
from configparser import ConfigParser


CONF_PATH = os.path.expanduser('~/.config/coachswarm/cctl.conf')


config = ConfigParser()


if len(config.read(CONF_PATH)) == 0:
    logging.error('Could not read %s. Please ensure it exists.', CONF_PATH)
    # TODO: Fix exit code
    sys.exit(-4)

# TODO: Should check for validity of the file before using it.


class Configuration:
    class CCTLD:
        @property
        def request_host(self) -> str:
            return config.get('cctld', 'request_host')

        @property
        def state_feed_host(self) -> str:
            return config.get('cctld', 'state_feed_host')

    @property
    def cctld(self) -> 'Configuration.CCTLD':
        return Configuration.CCTLD()
