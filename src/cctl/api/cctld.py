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


class CCTLDClient:
    """This ContextManager enables atomic, simple, async calls to the cctld
    server."""
    def __init__(self, ctx: zmq.asyncio.Context, cctl_ipc_path: str) -> None:
        self._ctx = ctx
        self._ipc = cctl_ipc_path
        self._socket = None

    async def __aenter__(self) -> 'CCTLDClient':
        self._socket = self._ctx.socket(zmq.REQ)
        self._socket.connect(self._ipc)
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        if exc_t is not None:
            return False
        if self._socket is not None:
            self._socket.disconnect(self._ipc)

    async def request(self, request: ipc.Request) -> ipc.Response:
        """Sends a request to the server and returns the response it gives
        back."""
        if self._socket is None:
            raise ValueError('The CCTLDClient class can only be used as a '
                             'context manager.')

        await self._socket.send_string(request.serialize())
        response_raw = await self._socket.recv_string()
        return ipc.Response.deserialize(response_raw)

    async def read_bot_state(self, bot: Coachbot) -> CoachbotState:
        """This function reads a Coachbot's state."""
        response = await self.request(ipc.Request(
            method='read',
            endpoint=f'/bots/{bot.identifier}/state'
        ))

        return CoachbotState.deserialize(response.body)
