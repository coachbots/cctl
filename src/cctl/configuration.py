# -*- coding: utf-8 -*-

"""Singleton module containing configuration values.

FIXME:
    Not cross platform due to using UNIX-like configuration.
"""

import sys
from os import makedirs, path
import logging
from configparser import ConfigParser
from importlib import resources

from cctl.res import ERROR_CODES, RES_STR

usr_conf_dir = path.join(path.expanduser('~'), '.config', 'coachswarm')

conf_file_paths = [
    path.join(usr_conf_dir, 'cctl.conf'),
    path.join('/', 'etc', 'coachswarm', 'cctl.conf'),
]

mandatory_keys = {
    'server': [
        'interface',
        'path'
    ],
    'coachswarm': [
        'conf_path'
    ]
}

config = ConfigParser()

# Attempt to read config if possible.
files_found = config.read(conf_file_paths)

if len(files_found) == 0:
    logging.warning(RES_STR['conf_error'])
    config = ConfigParser()
    config['server'] = {
        'interface': 'enp60s0',
        'path': '/home/hanlin/coach/server_beta'
    }
    config['coachswarm'] = {
        'conf_path': path.join(usr_conf_dir, 'coachswarm.conf')
    }

    if not path.exists(usr_conf_dir):
        makedirs(usr_conf_dir)

    # Write cctl.conf
    with open(path.join(usr_conf_dir, 'cctl.conf'), 'w') as conf_file:
        config.write(conf_file)

    # Write coachswarm.conf
    cs_conf_path = path.join(usr_conf_dir, 'coachswarm.conf')
    if not path.exists(cs_conf_path):
        with open(cs_conf_path, 'w') as conf_file:
            conf_file.write('{\n"COM_RANGE": 100.0\n}')

try:
    for key, values in mandatory_keys.items():
        assert key in config
        for value in values:
            assert value in config[key]
except AssertionError:
    logging.error(RES_STR['conf_malformed'])
    sys.exit(ERROR_CODES['conf_error'])


def get_server_dir():
    """Returns the operating server directory."""
    return config['server']['path']


def get_server_interface():
    """Returns the server interface"""
    return config['server']['interface']


def get_coachswarm_conf_path():
    """Returns the coachswarm.conf filepath"""
    return config['coachswarm']['conf_path']
