#!/usr/bin/env python

"""This module exposes all the endpoints that cctld exposes."""


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.2.1'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


import asyncio
import json
from typing import Any, Dict, List, Tuple, Union
import reactivex as rx
import zmq
import zmq.asyncio

from cctl.models import Coachbot
from cctl.models.coachbot import CoachbotState, Signal
from cctl.protocols import ipc
from cctl.utils.color import rgb_to_hex


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
            self._socket.setsockopt(zmq.LINGER, 0)
            self._socket.close()

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


class CCTLDRespEx(Exception):
    def __eq__(self, __o: object) -> bool:
        return self.__class__ == __o.__class__ and str(self) == str(__o)


class CCTLDRespInvalidState(CCTLDRespEx):
    pass


class CCTLDRespNotFound(CCTLDRespEx):
    """Returned by CCTLD when an endpoint is not found."""
    pass


class CCTLDRespBadRequest(CCTLDRespEx):
    """Returned by CCTLD when an invalid request is made."""
    pass


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

    @staticmethod
    def _raise_error_code(response: ipc.Response) -> None:
        if response.result_code == ipc.ResultCode.NOT_FOUND:
            raise CCTLDRespNotFound(response.body)
        if response.result_code == ipc.ResultCode.BAD_REQUEST:
            raise CCTLDRespBadRequest(response.body)
        if response.result_code != ipc.ResultCode.OK:
            raise CCTLDRespInvalidState(response.body)

    def __ensure_context(self):
        """This function is to ensure that this object is instantiated within a
        context manager, not to ensure a ZMQ context."""
        if self._ctx is None:
            raise ValueError('f{self.__class__.__name__} can only be used in '
                             'a context.')

    async def __aenter__(self) -> 'CCTLDClient':
        self._ctx = zmq.asyncio.Context()
        return self

    async def read_all_states(self) -> List[CoachbotState]:
        """Returns the latest bot states of all the robots.

        Returns:
            List[CoachbotState]: The list of all coachbot states.
        """
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='read',
                endpoint='/bots',
            ))
            if response.result_code != ipc.ResultCode.OK:
                raise CCTLDRespInvalidState('Invalid result code from cctld.')
            return [CoachbotState.from_dict(state) for state in
                    json.loads(response.body)]

    async def read_state(self, bot: Coachbot) -> CoachbotState:
        """This function returns the latest bot state according to ``cctld``.

        Parameters:
            bot (Coachbot): The target coachbot.

        Returns:
            CoachbotState: The state of the specified ``Coachbot``.
        """
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='read',
                endpoint=f'/bots/{bot.identifier}/state'
            ))
            return CoachbotState.deserialize(response.body)

    async def read_config(self) -> Dict[str, Any]:
        """Returns the configuration of ``cctld`` as it reports it."""
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='read',
                endpoint='/config'
            ))
            return json.loads(response.body)

    async def set_led_color(
        self,
        bot: Coachbot,
        color: Union[str, Tuple[int, int, int]]
    ) -> None:
        """Sets the color of the LED on the target coachbot.

        Parameters:
            bot (Coachbot): The target coachbot.
            color (3-element | str): The RGB value (0-255) of the robot. If
            string, then interpreted as a hex value
        """
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='update',
                endpoint=f'/bots/{bot.identifier}/led/color',
                body=(color if isinstance(color, str)
                      else rgb_to_hex(color))
            ))
            self.__class__._raise_error_code(response)

    async def set_is_on(self,
                        bot: Coachbot,
                        state: bool,
                        force: bool = False) -> None:
        """This function attempts to turn on a coachbot.

        Parameters:
            bot (Coachbot): The target coachbot.
            state (bool): Whether the coachbot should be on or not.
            force (bool): Whether to force the booting procedure.
        """
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='create' if state else 'delete',
                endpoint=f'/bots/{bot.identifier}/state/is-on',
                body=json.dumps({'force': force})
            ))
            self.__class__._raise_error_code(response)

    async def set_user_code_running(self, bot: Coachbot, state: bool) -> None:
        """This function sets the user code of the target bot to start or not,
        per the parameter.

        Parameters:
            bot (Coachbot): The target bot.
            state (bool): The target state.

        Raises:
            CCTLDRespInvalidState: If the user code could not be turned on due
            to a state conflict (likely the bot being powered off).
        """
        method = 'create' if state else 'delete'

        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method=method,
                endpoint=f'/bots/{bot.identifier}/user-code/running'
            ))
            self.__class__._raise_error_code(response)

    async def update_user_code(self, bot: Coachbot, user_code: str) -> None:
        """Attempts to update the user code on the specified bot.

        Raises:
            CCTLDRespInvalidState: If the robot is in an invalid state for
            updating. This likely means it is turned off.
        """
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='update',
                endpoint=f'/bots/{bot.identifier}/user-code/code',
                body=user_code
            ))
            self.__class__._raise_error_code(response)

    async def set_power_rail_on(self, state: bool) -> None:
        """Attempts to set the state of the power rail to on/off.

        Parameters:
            state (bool): The power rail target state.
        """
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='create' if state else 'delete',
                endpoint='/rail/is-on'
            ))
            self.__class__._raise_error_code(response)

    async def get_video_info(self) -> Dict[str, Dict[str, str]]:
        """Returns information about the video streams."""
        self.__ensure_context()
        assert self._ctx is not None
        with _CCTLDClientRequest(self._ctx, self._path) as req:
            response = await req.request(ipc.Request(
                method='read', endpoint='/info/video'))
            return json.loads(response.body)

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        if self._ctx is not None:
            self._ctx.destroy(0)
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

       my_observable, task = await CCTLDCoachbotStateObservable(
           'tcp://127.0.0.1:16791')
       my_observer = rx.Observer(on_next=lambda next: print(next))
       my_observable.subscribe(my_observer)
       await asyncio.wait([task])
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
            socket.disconnect(state_feed)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()
            context.destroy()

    return my_subject, asyncio.create_task(run())


async def CCTLDSignalObservable(
    signal_feed: str
) -> Tuple[rx.Subject, asyncio.Task]:
    """The ``CCTLDSignalObservable`` is an ``rx.Observable`` that will
    call the ``on_next`` function of your observer as new signals are fired by
    the coachbots.

    Note:
        This function will spawn an ``asyncio.Task`` that you are resonsible
        for managing. Failure to manage this task (possibly via cancelling it
        when you don't need it) will result in some overhead.

    Parameters:
        signal_feed (str): The URI to connect to the state feed. This should be
            the same signal feed **cctld** is serving on. Can be of the form
            ``ipc://<PATH>`` or ``tcp://<HOST>:<PORT>``.

    Returns:
        Tuple[reactivex.Subject, asyncio.Task]: The Observable and the running
        task.

    Example Usage:

    .. code-block:: python

       my_observable, taask = CCTLDSignalObservable()
       my_observer = rx.Observer(on_next=lambda next: print(next))
       my_observable.subscribe(my_observer)
    """
    my_subject = rx.Subject()

    async def run():
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(signal_feed)
        socket.setsockopt_string(zmq.SUBSCRIBE, '')
        try:
            while True:
                msg = Signal.from_dict(await socket.recv_json())
                my_subject.on_next(msg)
        except Exception as ex:
            my_subject.on_error(ex)
        finally:
            my_subject.on_completed()

    return my_subject, asyncio.create_task(run())
