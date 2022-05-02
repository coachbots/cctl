#!/usr/bin/env python

"""This is a hacky package that you can use to test your program. This
basically mocks a Coachbot at the networking level.

Todo:
    This is very bad and should be rewritten.
"""


import socket
import time
import json


from select import select
import zmq
from cctl.models import Coachbot
from cctl.models.coachbot import CoachbotState
from cctl.utils.math import Vec2


class MockManagedCoachbot(Coachbot):
    """Class used to mock a Coachbot listening for commands from cctld."""
    def __init__(
        self,
            state=CoachbotState(
                is_on=True,
                user_version='1',
                os_version='1',
                bat_voltage=4.2,
                position=Vec2(0, 0),
                theta=0,
                user_code_running=False
            )
    ):
        self.my_id = 90
        self.state = state
        self._5005sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._5005sock.settimeout(0.5)

        self.zmq_ctx = zmq.Context()

    def listen(self, timeout=1):
        """Listens for a timeout time for inputs.

        Todo:
            Cleanup this class, because most of this is simply copy pasted from
            legacy.
        """
        start_time = time.time()
        while (delta_t := time.time() - start_time) < timeout:
            print(f'[T+{round(delta_t, 1)}s]\t\t', end='')
            if not select([self._5005sock], [], [], 1e-1)[0]:
                print('No input as of now.')
                continue

            data, adr = self._5005sock.recvfrom(1024)
            dlist = data.decode().split('|')

            if dlist[0] == 'UPDATE' and dlist[1] != self.state.user_version:
                self.state.user_version = dlist[1].decode()
                # TODO: Need to actually mock user_code copying.
                print('Received UPDATE. '
                      f'user_version={self.state.user_version}')
                continue

            if dlist[0] == 'START_USR' and not self.state.user_code_running:
                self.state.user_code_running = True
                print('Received START_USR. '
                      f'user_code_running={self.state.user_code_running}')
                continue

            if dlist[0] == 'STOP_USR' and self.state.user_code_running:
                self.state.user_code_running = False
                print('Received STOP_USR. '
                      f'user_code_running={self.state.user_code_running}')
                continue

    def reply(self, timeout) -> None:
        target = 'tcp://192.168.1.119:16780'
        self._5006sock = self.zmq_ctx.socket(zmq.REQ)
        self._5006sock.connect(target)
        assert self.state.position is not None
        request = json.dumps({
            'identifier': self.my_id,
            'state': {
                'is_on': bool(self.state.is_on),
                'user_version': self.state.user_version,
                'os_version': self.state.os_version,
                'bat_voltage': self.state.bat_voltage,
                'position': [self.state.position.x, self.state.position.y],
                'theta': self.state.theta
            }
        })
        print(f'Sending request: {request} to {target}')
        self._5006sock.send_string(request)
        self._5006sock.RCVTIMEO = int(timeout * 1000)
        try:
            response = self._5006sock.recv()
            print(f'Received {response}')
        except zmq.error.Again:
            print('Server didn\'t reply.')
        finally:
            self._5006sock.close()

    def __enter__(self) -> 'MockManagedCoachbot':
        self._5005sock.bind(('localhost', 5005))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self._5005sock.close()
        return False
