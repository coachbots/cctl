#!/usr/bin/env python

"""This module exposes all the servers that cctld contains.

Currently, the following servers are exposed:
    * Status Server (``5678``, by default)
"""

import asyncio
import logging

from cctl.utils.net import get_ip_address
from cctld.conf import Config
from cctld.models import CoachbotState


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


async def start_management_server():
    """The ManagementServer is a simple server which receives the coach-os
    status via TCP. This is the server that communicates with Coachbots getting
    their data and metrics."""
    async def handle_client(reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        """This function handles a client asking a request to this server.
        """
        status = CoachbotState.deserialize(await reader.read())
        addr = writer.get_extra_info('peername')

        logging.getLogger('servers').debug('Received a status %s from %s',
                                           status, addr)

    server = await asyncio.start_server(
        handle_client,
        get_ip_address(Config().servers.interface),
        Config().servers.status_port
    )

    logging.getLogger('servers').debug('Started management_server')

    await server.serve_forever()
