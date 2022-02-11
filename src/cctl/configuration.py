# -*- coding: utf-8 -*-

"""Singleton module containing configuration values.

FIXME:
    Not cross platform due to using UNIX-like configuration.
"""

import sys
from os import makedirs, path
from typing import Tuple
import logging
from configparser import ConfigParser

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
    ],
    'camera': [
        'raw_dev_name',
        'processed_dev_name'
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
    config['camera'] = {
        'raw_dev_name': 'Piwebcam: UVC Camera',
        'processed_dev_name': 'Coachcam: Stream_Processed',
        'k1': -0.22,
        'k2': -0.022,
        'cx': 0.52,
        'cy': 0.5
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
    """
    Returns:
        The operating server directory.
    """
    return config['server']['path']


def get_server_interface():
    """
    Returns:
        The server interface
    """
    return config['server']['interface']


def get_coachswarm_conf_path():
    """
    Returns:
        The coachswarm.conf filepath
    """
    return config['coachswarm']['conf_path']


def get_camera_device_name() -> str:
    """
    Returns:
        The camera device name. This name is the name of the raw video stream
        recording the coachbots.
    """
    return config['camera']['raw_dev_name']


def get_processed_video_device_name() -> str:
    """
    Returns:
        The processed (ie. lens-corrected) video device name.
    """
    return config['camera']['processed_dev_name']


def get_camera_lens_correction_factors() -> Tuple[float, float, float, float]:
    """
    Returns:
        The camera correction factors in the format (k1, k2, cx, cy)
    """
    return (
        config.getfloat('camera', 'k1'),
        config.getfloat('camera', 'k2'),
        config.getfloat('camera', 'cx'),
        config.getfloat('camera', 'cy')
    )
