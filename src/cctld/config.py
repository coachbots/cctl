# -*- coding: utf-8 -*-

"""This module exposes configuration for the cctld process."""

from configparser import ConfigParser
import logging

from cctl.res import RES_STR

default_values = {
    'server': {
        'port': 6000
    }
}

config = ConfigParser()
files_found = config.read('/etc/coachswarm/cctld.conf')

if len(files_found) == 0:
    # TODO: Make a better error message.
    logging.error(RES_STR['conf_error'])

# TODO: Check if malformed file


def get_cctld_port():
    """Returns the port cctld should start on."""
    return config.get('server', 'port')
