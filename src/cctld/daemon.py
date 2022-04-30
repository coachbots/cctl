#!/usr/bin/env python

"""This small module exposes the main daemon that cctld uses."""

import daemon
from signal import SIGTERM, SIGHUP, SIGUSR1

from cctld.conf import Config

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.0.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


ctx = daemon.DaemonContext(
    working_directory=Config().general.workdir,
    umask=0o022,  # TODO: Change?
    pidfile='/var/run/cctld/cctld.pid',
    detach_process=None,  # Automatically handled
    prevent_core=True,  # Make sure we're not leaking sensitive info
    signal_map={
        SIGTERM: None,  # TODO: Change to cleanup program and exit
        SIGHUP: 'terminate',  # TODO: Change?
        SIGUSR1: None  # TODO: Change to reload conf
    }
)


def context() -> daemon.DaemonContext:
    """Returns the program daemon context."""
    return ctx
