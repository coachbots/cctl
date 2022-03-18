# -*- coding: utf-8 -*-

import daemon
from multiprocessing.connection import Listener

from cctld.config import get_cctld_port
from cctl import bots, bluetooth
from cctld.ipc import IPCMessage, IPCMessageState


def daemon_f():
    """The main daemon function. This function is the function that runs the
    daemon and that handles all the messages."""
    listener = Listener(('localhost', get_cctld_port()))
    conn = listener.accept()
    bt_interfaces = bluetooth.Interfaces()

    while True:
        msg = conn.recv()

        if msg == 'close':
            conn.close()
            break

        if isinstance(msg, IPCMessage):
            if isinstance(msg, IPCMessageState):
                bots.set_bot_on(msg.bot, msg.state)
                continue

    listener.close()


def main():
    """The main cctld function. This function spawns the daemon properly and
    should be used."""
    with daemon.DaemonContext():
        daemon_f()
