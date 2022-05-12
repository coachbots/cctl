#!/usr/bin/env python

"""This module exposes functions which send commands to coachbots."""

import logging
import traceback
from typing import Any, Callable, Coroutine, Tuple
import zmq
import zmq.asyncio

from cctl.protocols import coach_command


class CoachCommandError(Exception):
    """Represents an error that occurred when communicating with a Coachbot."""


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

    def _build_socket(self) -> zmq.asyncio.Socket:
        sock = self._context.socket(zmq.REQ)
        sock.setsockopt(zmq.RCVTIMEO, 100)
        sock.setsockopt(zmq.RCVTIMEO, 100)
        return sock

    def _close_socket(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    async def __aenter__(self) -> 'CoachCommand':
        self._socket = self._build_socket()
        return self

    async def close(self):
        self._close_socket()

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        await self.close()
        if exc_type is not None:
            print(f'{exc_type} executing a CoachCommand occurred. Value: '
                  f'{exc_value}')
            traceback.print_tb(exc_traceback)

    async def _execute_socket(
        self,
        function: Callable[[zmq.asyncio.Socket], Coroutine[Any, Any, Any]],
        max_retries: int = 3
    ) -> coach_command.Response:
        if self._socket is None:
            raise ValueError(f'{self.__class__.__name__} can only be used as '
                             'an atomic context manager.')

        async def _request(socket):
            for _ in range(max_retries):
                try:
                    await function(socket)
                    return
                except zmq.Again:
                    # TODO: Could be more informational.
                    logging.getLogger('coach-command').warning(
                        'Could not reach a coachbot. Retrying...')
            raise CoachCommandError('Could not make a request to the '
                                    'Coachbots.')

        async def _response(socket):
            for _ in range(max_retries):
                try:
                    reply = coach_command.Response.from_dict(
                        await socket.recv_json())
                    return reply
                except zmq.Again:
                    logging.getLogger('coach-command').warning(
                        'Did not receive a reply from a coachbot. Retrying...')
            raise CoachCommandError('Did not receive a reply from the '
                                    'Coachbot.')

        try:
            await _request(self._socket)
            return await _response(self._socket)
        finally:
            self._close_socket()

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

        async def worker(sock: zmq.asyncio.Socket):
            await sock.send_json(msg)
        await self._execute_socket(worker)

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

        async def worker(sock: zmq.asyncio.Socket):
            await sock.send_json(msg)
        response = await self._execute_socket(worker)

    async def set_led_color(self, value: Tuple[int, int, int]):
        """Sends a command to the coachbot to set the LED on or off."""
        msg = coach_command.Request('update', '/led/color',
                                    body={'color': value}).to_dict()

        async def worker(sock: zmq.asyncio.Socket):
            await sock.send_json(msg)
        response = await self._execute_socket(worker)
