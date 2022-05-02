#!/usr/bin/env python

"""This module exposes all the servers that cctld contains.

Currently, the following servers are exposed:
    * Status Server (``5678``, by default)
"""

import sys
import logging
from typing import Tuple
from cctld.models import AppState
from reactivex.subject import BehaviorSubject
import zmq
import zmq.asyncio

from cctld.conf import Config
from cctl.protocols import ipc, status
from cctl.models import CoachbotState
from cctld.res import ExitCode
from cctld.requests.handler import get as get_handler


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.0.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


async def start_ipc_request_server(app_state: AppState):
    """The IPCServer is a server that is used to communicate with other
    processes that may query the state of the Coachbots.

    Under the hood, this server uses ZMQ to ensure huge scalability.
    """
    async def handle_client(request: ipc.Request) -> ipc.Response:
        """This function handles a client asking a request to this server. """
        logging.getLogger('servers').debug('Received IPC request %s', request)

        if request.method not in ipc.VALID_METHODS:
            return ipc.Response(ipc.ResultCode.BAD_REQUEST)

        try:
            handler, matchs = get_handler(request.endpoint, request.method)
            return handler(app_state, request, tuple(matchs))
        except KeyError:
            logging.getLogger('servers').warning(
                'Invalid method %s requested by %s.', request.method,
                'client'  # TODO: Get client name/PID.
            )
            return ipc.Response(ipc.ResultCode.METHOD_NOT_ALLOWED)
        except ValueError:
            return ipc.Response(ipc.ResultCode.NOT_FOUND)

    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REP)
    try:
        sock.bind(Config().ipc.request_feed)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to the requested UNIX file %s. Please check '
            'permissions. Error: %s', Config().ipc.request_feed, zmq_err)
        sys.exit(ExitCode.EX_NOPERM)

    while True:
        request = await sock.recv_string()
        response = await handle_client(ipc.Request.deserialize(request))
        logging.getLogger('servers').debug('Responding with: %s', response)
        await sock.send_string(response.serialize())


async def start_status_server(app_state: AppState) -> None:
    """The StatusServer is a simple server which receives the coach-os
    status via TCP. This is the server that communicates with Coachbots getting
    their data and metrics.

    Parameters:
        reactivex.subjects.BehaviorSubject: The subject to inject
        ``CoachbotState``s into.
    """
    async def handle_client(request: status.Request) -> status.Response:
        """This function handles a client asking a request to this server."""
        logging.getLogger('servers').debug('Received Status request %s',
                                           request)

        req_id, new_state = request.identifier, request.state

        old_states = app_state.coachbot_states.value
        app_state.coachbot_states.on_next(
            tuple(new_state
                  if i == req_id
                  else old_state
                  for i, old_state in enumerate(old_states))
        )

        return status.Response()

    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REP)
    try:
        sock.bind(Config().servers.status_host)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to %s. Pleease check whether another '
            'process is using it. Error: %s',
            Config().servers.status_host, zmq_err)
        sys.exit(ExitCode.EX_UNAVAILABLE)

    while True:
        request = await sock.recv_string()

        response = await handle_client(status.Request.deserialize(request))
        logging.getLogger('servers').debug('Responding with: %s', response)
        await sock.send_string(response.serialize())


async def start_ipc_feed_server(app_state: AppState) -> None:
    """This function starts the IPC feed server on the requested feed. This
    will end up being a ``zmq.PUB`` transprort that will publish its data every
    time relevant ``reactivex.subject``s change their value."""
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.PUB)
    try:
        sock.bind(Config().ipc.state_feed)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to %s. Please check whether you have permissions.'
            'Error: %s',
            Config().ipc.state_feed, zmq_err)
        sys.exit(ExitCode.EX_NOPERM)

    def on_coachbot_state_change(new_states: Tuple[CoachbotState, ...]):
        sock.send_json([new_state.to_dict() for new_state in new_states])

    app_state.coachbot_states.subscribe(on_next=on_coachbot_state_change)
