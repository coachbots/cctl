#!/usr/bin/env python

"""This is a hacky package that you can use to test your program. This
basically mocks a Coachbot at the networking level.

Todo:
    This is very bad and should be rewritten.
"""


import socket
import time

from zmq.sugar.poll import select
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
        self.state = state
        self._5005sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._5005sock.settimeout(0.5)

    def listen(self, timeout=1):
        """Listens for a timeout time for inputs.

        Todo:
            Cleanup this class, because most of this is simply copy pasted from
            legacy.
        """
        start_time = time.time()
        while (delta_t := time.time() - start_time) < timeout:
            print(f'[T+{round(delta_t, 2)}s]\t\t', end='')
            if not select([self._5005sock], [], [], 0)[0]:
                time.sleep(1)
                print('No input as of now.')
                continue

            data, adr = self._5005sock.recvfrom(1024)
            dlist = data.split(b'|')

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

    def __enter__(self) -> 'MockManagedCoachbot':
        self._5005sock.bind(('', 5005))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self._5005sock.close()
        return False
