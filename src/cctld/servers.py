#!/usr/bin/env python

"""This module exposes all the servers that cctld contains.

Currently, the following servers are exposed:
    * Status Server (``5678``, by default)
"""

import sys
import re
import logging
from typing import Any, Callable, Dict, Tuple, Union
from dataclasses import replace
import reactivex as rx
import zmq
import zmq.asyncio
from cctl.utils.math import Vec2

from cctl.utils.net import get_ip_address
from cctld.conf import Config
from cctl.protocols import ipc, status
from cctld.res import ExitCode


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

IPCHandler = Callable[[Any, ipc.Request, Tuple[Union[str, Any]]], Any]
ENDPOINT_HANDLERS: Dict[str, Dict[str, IPCHandler]] = {
    r'/bots/([0-9]+)/state/?': {
        'read': lambda state, _, endpoint_groups: ipc.Response(
            ipc.ResultCode.OK,
            state.bot_states[int(endpoint_groups[1])]
        ),
    },
    r'/bots/state/?': {
        'read': lambda state, _, __: ipc.Response(ipc.ResultCode.OK)
    }
}


async def start_ipc_server(state_subject: rx.subjects.BehaviorSubject):
    """The IPCServer is a server that is used to communicate with other
    processes that may query the state of the Coachbots.

    Under the hood, this server uses ZMQ to ensure huge scalability.
    """
    async def handle_client(request: ipc.Request) -> ipc.Response:
        """This function handles a client asking a request to this server. """
        logging.getLogger('servers').debug('Received IPC request %s', request)

        for endpoint_regex, handlers in ENDPOINT_HANDLERS.items():
            match = re.match(endpoint_regex, request.endpoint)
            if not match:
                continue

            if request.method not in ipc.VALID_METHODS:
                return ipc.Response(ipc.ResultCode.BAD_REQUEST)

            try:
                state = state_subject.value
                return handlers[request.method](state, request, match.groups())
            except KeyError:
                logging.getLogger('servers').warning(
                    'Invalid method %s requested by %s.', request.method,
                    'client'  # TODO: Get client name/PID.
                )
                return ipc.Response(ipc.ResultCode.METHOD_NOT_ALLOWED)

        return ipc.Response(ipc.ResultCode.NOT_FOUND)

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
        response = await handle_client(ipc.Request.deserialize(request))
        logging.getLogger('servers').debug('Responding with: %s', response)
        await sock.send_string(response.serialize())


async def start_status_server(state_subject: rx.subjects.BehaviorSubject):
    """The StatusServer is a simple server which receives the coach-os
    status via TCP. This is the server that communicates with Coachbots getting
    their data and metrics."""
    async def handle_client(request: status.Request) -> status.Response:
        """This function handles a client asking a request to this server. """
        logging.getLogger('servers').debug('Received Status request %s',
                                           request)

        id, status = request.identifier, request.status

        state_subject.on_next(
            replace(
                state_subject.value,
                bot_states=(
                    (v := state_subject.value)[:id] + (status, ) + v[(id +1 ):]
                )
            )
        )

        return status.Response()


    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REP)
    try:
        sock.bind(f'tcp://{get_ip_address(Config().servers.interface)}'
                  f':{Config().servers.status_port}')
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to tcp://%s:%d. Pleease check whether another '
            'process is using it. Error: %s',
            get_ip_address(Config().servers.interface),
            Config().servers.status_port,
            zmq_err)
        sys.exit(ExitCode.EX_UNAVAILABLE)

    while True:
        request = await sock.recv_string()
        response = await handle_client(CoachbotState.deserialize(request))
        logging.getLogger('servers').debug('Responding with: %s', response)
        await sock.send_string(response.serialize())
