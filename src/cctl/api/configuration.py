# -*- coding: utf-8 -*-

"""
Singleton module containing configuration values.
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
        'conf_path',
        'remote_path',
        'id_range_min',
        'id_range_max',
        'ssh_user',
        'ssh_key',
        'net_server_port_pub',
        'net_server_port_rep',
        'net_server_port_req'
    ],
    'camera': [
        'raw_dev_name',
        'processed_dev_name'
    ],
    'logs': [
        'syslog_path',
        'legacy_log_file_path'
    ]
}

default_values = {
    'server': {
        'interface': 'enp60s0',
        'path': '/home/hanlin/coach/server_beta'
    },
    'coachswarm': {
        'conf_path': path.join(usr_conf_dir, 'coachswarm.conf'),
        'remote_path': '/home/hanlin/control',
        'id_range_min': 0,
        'id_range_max': 99,
        'ssh_user': 'pi',
        'ssh_key': path.join(path.expanduser('~'), '.ssh', 'id_coachbot'),
        'net_server_port_rep': 16891,
        'net_server_port_pub': 16892,
        'net_server_port_req': 16893
    },
    'camera': {
        'raw_dev_name': 'Piwebcam: UVC Camera',
        'processed_dev_name': 'Coachcam: Stream_Processed',
        'k1': -0.22,
        'k2': -0.022,
        'cx': 0.52,
        'cy': 0.5
    },
    'logs': {
        'syslog_path': '/var/log/syslog',
        'legacy_log_file_path': '/home/pi/control/experiment_log'
    }
}

config = ConfigParser()

# Attempt to read config if possible.
files_found = config.read(conf_file_paths)

if len(files_found) == 0:
    logging.warning(RES_STR['conf_error'])
    config = ConfigParser()

    config.update(default_values)

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


def _exit_on_err_key(m_key: str):
    logging.error(RES_STR['conf_malformed'], m_key)
    sys.exit(ERROR_CODES['conf_error'])


for key, values in mandatory_keys.items():
    if key not in config:
        _exit_on_err_key(key)

    for value in values:
        if value not in config[key]:
            _exit_on_err_key(value)


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


def get_syslog_path() -> str:
    """Returns the syslog path.

    Returns:
        str: The user-configured syslog path.
    """
    return config.get('logs', 'syslog_path')


def get_legacy_log_file_path() -> str:
    """Returns the legacy log file name.

    This filename is the filename cctl expects legacy logs to be called on the
    coachbots.

    Returns:
        str: The user configured legacy log filename.
    """
    return config.get('logs', 'legacy_log_file_path')


def get_coachswarm_ssh_user() -> str:
    """Returns the ssh user to use for the coachbots."""
    return config.get('coachswarm', 'ssh_user')


def get_coachswarm_path_to_ssh_key() -> str:
    """Returns the path to the coachbot ssh key."""
    return path.expanduser(config.get('coachswarm', 'ssh_key'))


def get_valid_coachbot_range():
    """Returns the valid Coachbot range."""
    return range(
        config.getint('coachswarm', 'id_range_min'),
        config.getint('coachswarm', 'id_range_max') + 1
    )


def get_coachswarm_net_rep_port() -> int:
    """Returns the port used for the networking with the coachbots on the REP
    transport."""
    return config.getint('coachswarm', 'net_server_port_rep')


def get_coachswarm_net_pub_port() -> int:
    """Returns the port used for networking with the coachbots on the PUB
    transport."""
    return config.getint('coachswarm', 'net_server_port_pub')


def get_coachswarm_net_req_port() -> int:
    """Returns the port used for networking with the coachbots on the REQ
    transport."""
    return config.getint('coachswarm', 'net_server_port_req')


def get_coachswarm_remote_path() -> str:
    """Returns the path to the remote directory."""
    return config.get('coachswarm', 'remote_path')
