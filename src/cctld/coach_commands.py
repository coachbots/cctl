#!/usr/bin/env python

"""This module exposes functions which send commands to coachbots."""

import traceback
from typing import Any, Callable, Tuple
import zmq
import zmq.asyncio

from cctl.protocols import coach_command


class CoachCommand:
    def __init__(self, host: str, coachbot_command_port: int) -> None:
        """Initializes a CoachCommand.

        Parameters:
            host (str): The host location of the coachbot.
            coachbot_command_port (int): The port to which the commands are to
            be sent.
        """
        self._host = host
        self._port = coachbot_command_port
        self._context = zmq.asyncio.Context()

    async def __aenter__(self) -> 'CoachCommand':
        self._socket = self._context.socket(zmq.REQ)
        return self

    async def close(self):
        if self._socket is not None:
            self._socket.close()

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await self.close()
        if exc_type is not None:
            print(f'{exc_type} executing a CoachCommand occurred. Value: '
                  f'{exc_value}')
            traceback.print_tb(exc_traceback)

    async def _execute_socket(
        self,
        function: Callable[[zmq.Socket], Any]) -> coach_command.Response:
        if self._socket is None:
            raise ValueError(f'{self.__class__.__name__} can only be used as '
                             'an atomic context manager.')
        function(self._socket)
        reply = coach_command.Response.from_dict(
            await self._socket.recv_json())
        self._socket = None
        return reply

    async def set_user_code_running(self, value: bool):
        """Sends the start/stop user code command.

        Parameters:
            value (bool): Whether the user code should run or not.

        Todo:
            Rewrite. Implementation is currently legacy.
        """
        msg = coach_command.Request(
            'create' if value else 'delete',
            '/user-code/running'
        ).to_dict()
        await self._execute_socket(lambda sock: sock.send_json(msg))

    async def set_user_code(self, value: str):
        """Sends a new user code to the coachbot.

        Parameters:
            value (str): The user code to be executed. Must be a valid python
            program.

        Todo:
            Rewrite. Legacy implementation.
        """
        msg = coach_command.Request('update', '/user-code/code',
                                    body={'code': value}).to_dict()
        response = await self._execute_socket(lambda s: s.send_json(msg))

    async def set_led_color(self, value: Tuple[int, int, int]):
        """Sends a command to the coachbot to set the LED on or off."""
        msg = coach_command.Request('update', '/led/color',
                                    body={'color': value}).to_dict()
        response = await self._execute_socket(lambda s: s.send_json(msg))
