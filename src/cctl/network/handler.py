# -*- coding: utf-8 -*-

"""This module exposes the base NetworkEventHandler."""

from logging import Logger
import base64
from threading import Thread
import threading
from typing import Callable, Tuple
import zmq

from cctl.api.configuration import get_coachswarm_net_rep_port, \
    get_server_interface
from cctl.netutils import get_ip_address


class NetworkEventHandler:
    """This class exposes functions for handling network events, including
    sending signals and registering for events.

    The API of this class is exposed via a signal/slot paradigm (similar to
    QT). There are two key elements in using this class effectively:
        * Sending signals, achieved with NetworkEventHandler.signal()
        * Hooking into slots, achieved with NetworkEventHandler.add_slot()

    Sending signals raises the signal on all devices managed by this handler.
    When this signal is raised, all slots registered for that sig_type are
    called.
    """

    # The maximum signal type size.
    SIGNAL_NAME_SIZE = 16

    class WorkerThread(Thread):
        """The actual worker thread of the NetworkEventHandler."""
        MAX_SLEEP_TIME = 1

        def __init__(self, network_handler: 'NetworkEventHandler',
                     *args, **kwargs) -> None:
            Thread.__init__(self, *args, **kwargs)
            self.network_handler = network_handler
            self.daemon = True
            self._stop_event = threading.Event()
            self.start()

        def stop(self) -> None:
            """Raises the flag that stops the thread. If the thread is
            currently processing a message, it will first finish processing it
            and then close."""
            self._stop_event.set()

        def get_is_stopped(self) -> bool:
            """Returns whether the thread is stopped."""
            return self._stop_event.is_set()

        def run(self):
            while not self.get_is_stopped():
                # TODO: Test this
                data = self.network_handler.rep_socket.recv()
                signal, message = NetworkEventHandler.decode_signal_msg(data)
                self.network_handler.exec_handler(signal, message)

    def __init__(self):
        self._zmq_contexts = {
            'req': zmq.Context(),
            'rep': zmq.Context(),
            'pub': zmq.Context()
        }
        self._sockets = {
            'req': self._zmq_contexts['req'].socket(zmq.REQ),
            'rep': self._zmq_contexts['rep'].socket(zmq.REP),
            'pub': self._zmq_contexts['pub'].socket(zmq.PUB)
        }
        self._handlers = {}

        self._bind_rep_socket()
        self.worker = NetworkEventHandler.WorkerThread(self)

    @property
    def req_socket(self) -> zmq.Socket:
        """The ZMQ request socket."""
        return self._sockets['req']

    @property
    def rep_socket(self) -> zmq.Socket:
        """The ZMQ response socket."""
        return self._sockets['rep']

    @property
    def pub_socket(self) -> zmq.Socket:
        """The ZMQ pub socket."""
        return self._sockets['pub']

    def get_handler(self, signal: str) -> Callable[[str, bytes], None]:
        """Returns the handler for the given signal."""
        return self._handlers[signal]

    def exec_handler(self, signal: str, message: bytes) -> None:
        """Executes the handler for the given signal."""
        self.get_handler(signal)(signal, message)

    def _bind_rep_socket(self) -> None:
        """Binds the REP socket."""
        self.rep_socket.bind(
            f'tcp://{get_ip_address(get_server_interface())}:' +
            str(get_coachswarm_net_rep_port()))

    def signal(self, sig_type: str, message: bytes) -> None:
        """This method sends out a signal.

        Warning:
            sig_type cannot exceed the size of
            NetworkEventHandler.SIGNAL_NAME_SIZE which is currently 16 and it
            must be ascii encodable.

            sig_type should never start with a null character (unlikely to
            happen in day to day use).

        Raises:
            ValueError: If sig_type is not ascii encodable or its size is
            greater than NetworkEventHandler.SIGNAL_NAME_SIZE
        """
        self.pub_socket.send(
            NetworkEventHandler.encode_signal_msg(sig_type, message))

    def add_slot(self, sig_type: str,
                 handler: Callable[[str, bytes], None]) -> None:
        """Registers a slot to handle the specified sig_type.

        Parameters:
            sig_type (str): The signal to be handled.
            handler (Callble): The signal handler.
        """
        try:
            self._handlers[sig_type] += [handler]
        except KeyError:
            self._handlers[sig_type] = [handler]

    @staticmethod
    def log_handler(logger: Logger, sig_type: str, message: bytes) -> None:
        """A simple log_handler that logs to the specified logger."""
        logger.info('NetworkEventHandler handling signal %s. Message is: %s',
                    sig_type, str(message))

    @staticmethod
    def encode_signal_msg(sig_type: str, message: bytes) -> bytes:
        """Encodes a signal message into raw bytes to be sent.

        Raises:
            ValueError: If the signal type is too long.
        """
        sig_bytes = sig_type.encode('ascii')

        if len(sig_bytes) > NetworkEventHandler.SIGNAL_NAME_SIZE:
            raise ValueError

        sig = sig_bytes.ljust(NetworkEventHandler.SIGNAL_NAME_SIZE, b'\0')

        return base64.b64encode(sig + message)

    @staticmethod
    def decode_signal_msg(data: bytes) -> Tuple[str, bytes]:
        """Decodes a signal message into signal type and data.

        Parameters:
            data (bytes): The data

        Returns:
            Tuple[str, bytes]: The signal name and the message data
        """
        signal_b = data[:NetworkEventHandler.SIGNAL_NAME_SIZE].lstrip(b'\0')

        signal = signal_b.decode('ascii')
        message = data[:NetworkEventHandler.SIGNAL_NAME_SIZE]

        return signal, message

    def tear_down(self) -> None:
        """Tears down the NetworkEventHandler. This is also hooked into
        __del__, so you don't necessarily need to call this manually."""
        self.worker.stop()

    def __del__(self):
        self.tear_down()
