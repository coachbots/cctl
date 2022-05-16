#!/usr/bin/env python

"""This module exposes all the servers that cctld contains.

Currently, the following servers are exposed:
    * Status Server (``5678``, by default)
"""

import sys
import logging
from typing import Tuple

import zmq
import zmq.asyncio

from cctld.models import AppState
from cctl.protocols import ipc, status
from cctl.models import CoachbotState, Signal
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


async def _retried_reply(sock, reply: str, max_n: int) -> int:
    for _ in range(max_n):
        try:
            await sock.send_string(reply)
            return 0
        except zmq.Again:
            pass
    logging.getLogger('servers').warning(
        'Could not send status reply message. Failing')
    return -1


async def start_ipc_request_server(app_state: AppState):
    """The IPCServer is a server that is used to communicate with other
    processes that may query the state of the Coachbots.

    Under the hood, this server uses ZMQ to ensure huge scalability.
    """
    # Detrmines the maximum number of attempts to reply.
    max_rep_retry = 3

    async def handle_client(request: ipc.Request) -> ipc.Response:
        """This function handles a client asking a request to this server. """
        logging.getLogger('servers').debug('Received IPC request %s', request)

        if request.method not in ipc.VALID_METHODS:
            return ipc.Response(ipc.ResultCode.BAD_REQUEST)

        try:
            handler, matchs = get_handler(request.endpoint, request.method)
        except KeyError:
            logging.getLogger('servers').warning(
                'Invalid method %s requested by %s.', request.method,
                'client'  # TODO: Get client name/PID.
            )
            return ipc.Response(ipc.ResultCode.METHOD_NOT_ALLOWED)
        except ValueError:
            return ipc.Response(ipc.ResultCode.NOT_FOUND)

        response = await handler(app_state, request, tuple(matchs))
        logging.getLogger('servers').debug('Returning IPC response %s',
                                           response)
        return response

    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REP)
    sock.setsockopt(zmq.SNDTIMEO, 100)
    try:
        sock.bind(app_state.config.ipc.request_feed)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to the requested UNIX file %s. Please check '
            'permissions. Error: %s',
            app_state.config.ipc.request_feed, zmq_err)
        sys.exit(ExitCode.EX_NOPERM)

    while True:
        request_raw = await sock.recv_string()
        request = ipc.Request.deserialize(request_raw)
        response = await handle_client(request)
        logging.getLogger('servers').debug('Responding with: %s', response)
        await _retried_reply(sock, response.serialize(), max_rep_retry)


async def start_status_server(app_state: AppState) -> None:
    """The StatusServer is a simple server which receives the coach-os
    status via TCP. This is the server that communicates with Coachbots getting
    their data and metrics.

    Parameters:
        app_state (AppState): The application state.
    """
    # Detrmines the number of retries attempted before giving up on a reply.
    max_rep_retry = 3

    async def handle_client(request: status.Request) -> status.Response:
        """This function handles a client asking a request to this server."""

        if request.type == 'signal':
            assert isinstance(request.body, Signal)
            logging.getLogger('servers').debug('Signal=%s', request.body)
            app_state.coachbot_signals.on_next(request.body)
            return status.Response()

        if request.type == 'state':
            req_id, new_state = request.identifier, request.body
            logging.getLogger('servers').debug(
                'State request %d=%s', req_id, new_state)

            assert isinstance(new_state, CoachbotState)
            app_state.coachbot_states.get_subject(req_id).on_next(
                (req_id, new_state))

            return status.Response()

        return status.Response(status_code=status.StatusCode.OK)

    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.REP)
    sock.setsockopt(zmq.SNDTIMEO, 100)
    try:
        sock.bind(app_state.config.servers.status_host)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to %s. Please check whether another '
            'process is using it. Error: %s',
            app_state.config.servers.status_host, zmq_err)
        sys.exit(ExitCode.EX_UNAVAILABLE)

    while True:
        request_raw = await sock.recv_string()
        request = status.Request.deserialize(request_raw)

        response = await handle_client(request)
        logging.getLogger('servers').debug('Responding with: %s', response)

        await _retried_reply(sock, response.serialize(), max_rep_retry)


async def start_ipc_feed_server(app_state: AppState) -> None:
    """This function starts the IPC feed server on the requested feed. This
    will end up being a ``zmq.PUB`` transprort that will publish its data every
    time relevant ``reactivex.subject``s change their value."""
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.PUB)
    try:
        sock.bind(app_state.config.ipc.state_feed)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to %s. Please check whether you have permissions.'
            'Error: %s',
            app_state.config.ipc.state_feed, zmq_err)
        sys.exit(ExitCode.EX_NOPERM)

    def on_coachbot_state_change(new_states: Tuple[CoachbotState, ...]):
        sock.send_json([new_state.to_dict() for new_state in new_states])

    def close():
        logging.getLogger('servers').info('Closing IPC Feed Server.')
        sock.close()

    app_state.coachbot_states.subscribe(on_next=on_coachbot_state_change,
                                        on_completed=close,
                                        on_error=lambda _: close())


async def start_ipc_signal_forward_server(app_state: AppState) -> None:
    """This server forwards signals that ``Coachbots`` send to **cctld** into
    the registered feed. APIs can then listen for these to trigger events.
    """
    ctx = zmq.asyncio.Context()
    sock = ctx.socket(zmq.PUB)

    try:
        sock.bind(app_state.config.ipc.signal_feed)
    except zmq.ZMQError as zmq_err:
        logging.getLogger('servers').error(
            'Could not bind to %s. Please check whether you have permissions.'
            'Error: %s',
            app_state.config.ipc.state_feed, zmq_err)
        sys.exit(ExitCode.EX_NOPERM)

    def on_signal(signal: Signal):
        sock.send_json(signal.to_dict())

    def close():
        logging.getLogger('servers').info('Closing IPC Signal Forward Server.')
        sock.close()

    app_state.coachbot_signals.subscribe(on_next=on_signal,
                                         on_completed=close,
                                         on_error=lambda _: close())
