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


import asyncio
from typing import Tuple
import reactivex as rx
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


async def CCTLDCoachbotStateObservable(
    state_feed: str) -> Tuple[rx.Subject, asyncio.Task]:
    """The ``CCTLDCoachbotStateObservable`` is an ``rx.Observable`` that will
    call the ``on_next`` function of your observer as new ``CoachbotState``
    data comes through.

    Note:
        This function will spawn an ``asyncio.Task`` that you are resonsible
        for managing. Failure to manage this task (possibly via cancelling it
        when you don't need it) will result in some overhead.

    Parameters:
        state_feed (str): The URI to connect to the state feed. This should be
            the same state feed **cctld** is serving on. Can be of the form
            ``ipc://<PATH>`` or ``tcp://<HOST>:<PORT>``.

    Returns:
        Tuple[reactivex.Subject, asyncio.Task]: The Observable and the running
        task.

    Example Usage:

    .. code-block:: python

       my_observable, task = CCTLDCoachbotStateObservable()
       my_observer = rx.Observer(on_next=lambda next: print(next))
       my_observable.subscribe(my_observer)
    """
    my_subject = rx.Subject()

    async def run():
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(state_feed)
        socket.setsockopt_string(zmq.SUBSCRIBE, '')
        try:
            while True:
                msg = [CoachbotState.from_dict(bot)
                       for bot in (await socket.recv_json())]
                my_subject.on_next(msg)
        except Exception as ex:
            my_subject.on_error(ex)
        finally:
            my_subject.on_completed()

    return my_subject, asyncio.create_task(run())
