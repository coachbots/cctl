#!/usr/bin/env python

"""This module exposes all the servers that cctld contains.

Currently, the following servers are exposed:
    * Status Server (``5678``, by default)
"""

import sys
import asyncio
import re
import logging
from typing import Any, Callable, Dict, Tuple, Union
import zmq
import zmq.asyncio
from cctl.utils.math import Vec2

from cctl.utils.net import get_ip_address
from cctld.conf import Config
from cctl.models import IPC_VALID_METHODS, CoachbotState, IPCRequest, \
    IPCResponse, IPCResultCode
from cctld.res import ExitCode


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

IPCHandler = Callable[[IPCRequest, Tuple[Union[str, Any], ...]], Any]
ENDPOINT_HANDLERS: Dict[str, Dict[str, IPCHandler]] = {
    r'/bots/([0-9]+)/state/?': {
        'read': lambda _, __: IPCResponse(
            IPCResultCode.OK,
            CoachbotState(
                is_on=True,
                user_version='0.1.0',
                os_version='0.1.0',
                bat_voltage=3.7,
                position=Vec2(0.3, 0.4),
                theta=0
            ).serialize()
        ),
    },
    r'/bots/state/?': {
        'read': lambda _, __: IPCResponse(IPCResultCode.OK)
    }
}


async def start_ipc_server():
    """The IPCServer is a server that is used to communicate with other
    processes that may query the state of the Coachbots.

    Under the hood, this server uses ZMQ to ensure huge scalability.
    """
    async def handle_client(request: IPCRequest) -> IPCResponse:
        """This function handles a client asking a request to this server. """
        logging.getLogger('servers').debug('Received IPC request %s', request)

        for endpoint_regex, handlers in ENDPOINT_HANDLERS.items():
            match = re.match(endpoint_regex, request.endpoint)
            if not match:
                continue

            if request.method not in IPC_VALID_METHODS:
                return IPCResponse(IPCResultCode.BAD_REQUEST)

            try:
                return handlers[request.method](request, match.groups())
            except KeyError:
                logging.getLogger('servers').warning(
                    'Invalid method %s requested by %s.', request.method,
                    'client'  # TODO: Get client name/PID.
                )
                return IPCResponse(IPCResultCode.METHOD_NOT_ALLOWED)

        return IPCResponse(IPCResultCode.NOT_FOUND)

    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REP)
    try:
        sock.bind(f'ipc://{Config().ipc.path}')
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to the requested UNIX file %s. Please check '
            'permissions. Error: %s', Config().ipc.path, zmq_err)
        sys.exit(ExitCode.EX_NOPERM)

    while True:
        request = await sock.recv_string()
        response = await handle_client(IPCRequest.deserialize(request))
        logging.getLogger('servers').debug('Responding with: %s', response)
        await sock.send_string(response.serialize())


async def start_management_server():
    """The ManagementServer is a simple server which receives the coach-os
    status via TCP. This is the server that communicates with Coachbots getting
    their data and metrics."""
    async def handle_client(reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        """This function handles a client asking a request to this server. """
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

    async with server:
        await server.serve_forever()
