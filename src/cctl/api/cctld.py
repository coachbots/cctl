#!/usr/bin/env python

"""This module exposes all the endpoints that cctld exposes."""


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


import zmq
import zmq.asyncio

from cctl.api.bot_ctl import Coachbot
from cctl.models.coachbot import CoachbotState
from cctl.protocols import ipc


class _CCTLDClientRequest:
    """This ContextManager enables atomic, simple, async calls to the cctld
    server.
    """
    def __init__(self, ctx: zmq.asyncio.Context, cctl_ipc_path: str) -> None:
        self._ctx = ctx
        self._ipc = cctl_ipc_path
        self._socket = None

    def __enter__(self) -> '_CCTLDClientRequest':
        self._socket = self._ctx.socket(zmq.REQ)
        self._socket.connect(self._ipc)
        return self

    def __exit__(self, exc_t, exc_v, exc_tb):
        if self._socket is not None:
            self._socket.disconnect(self._ipc)

        return False

    async def request(self, request: ipc.Request) -> ipc.Response:
        """Sends a request to the server and returns the response it gives
        back."""
        if self._socket is None:
            raise ValueError('The CCTLDClient class can only be used as a '
                             'context manager.')

        await self._socket.send_string(request.serialize())
        response_raw = await self._socket.recv_string()
        return ipc.Response.deserialize(response_raw)


class CCTLDClient:
    """The ``CCTLDClient`` object is a ``ContextManager`` that manages requests
    automatically for you. Use it as any other ``ContextManager``. All other
    use is prohibited.

    For example:

    .. code-block:: python

       async with CCTLDClient('ipc:///var/run/cctld/request_feed') as client:
           print(await client.read_bot_state())
           # Let's pretend we're doing something here.
           await asyncio.sleep(10)
           print(await client.read_bot_state())
    """
    def __init__(self, cctl_ipc_path: str) -> None:
        self._path = cctl_ipc_path
        self._ctx = None

    async def __aenter__(self) -> 'CCTLDClient':
        self._ctx = zmq.asyncio.Context()
        return self

    async def read_bot_state(self, bot: Coachbot) -> CoachbotState:
        """This function returns the latest bot state according to ``cctld``.

        Returns:
            CoachbotState: The state of the specified ``Coachbot``.
        """
        if self._ctx is None:
            raise ValueError('CCTLDClient can only be used as a context '
                             'manager. ')
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='read',
                endpoint=f'/bots/{bot.identifier}/state'
            ))
            return CoachbotState.deserialize(response.body)

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        return False
