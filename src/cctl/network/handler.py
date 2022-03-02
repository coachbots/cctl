# -*- coding: utf-8 -*-

"""This module exposes the base NetworkEventHandler."""

from enum import Enum
from logging import Logger
import base64
import logging
from threading import Thread
import threading
from typing import Callable, Optional, Tuple, List
import zmq
from time import time
from cctl.api.bot_ctl import Coachbot

from cctl.api.configuration import get_coachswarm_net_rep_port, \
    get_coachswarm_net_pub_port, get_coachswarm_net_req_port, \
    get_server_interface
from cctl.netutils import get_ip_address
from cctl.network.exit_codes import NetStatus
from cctl.res import RES_STR


def _tcpurl(address: str, port: int) -> str:
    return f'tcp://{address}:{port}'


class NetworkResponses(Enum):
    """Presents the valid responses a handler may return."""
    SUCCESS = 0
    ERR_REPEAT = 1


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

    # The maximum id size
    IDENTIFIER_SIZE = 4

    # The total size of the receive header
    RECV_SIZE = SIGNAL_NAME_SIZE + IDENTIFIER_SIZE

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
                result = self.network_handler.exec_handler(
                    *NetworkEventHandler.decode_signal_msg(data))
                result = result if result is not None \
                    else NetworkResponses.SUCCESS
                self.network_handler.rep_socket.send(bytes(result.value))

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
        self._bind_pub_socket()
        self.worker = NetworkEventHandler.WorkerThread(self)

    def _bind_rep_socket(self) -> None:
        """Binds the REP socket."""
        address = _tcpurl(get_ip_address(get_server_interface()),
                          get_coachswarm_net_rep_port())
        logging.debug(RES_STR['logging']['rep_bind'], address)
        self.rep_socket.bind(address)

    def _bind_pub_socket(self) -> None:
        """Binds the PUB socket."""
        address = _tcpurl(get_ip_address(get_server_interface()),
                          get_coachswarm_net_pub_port())
        logging.debug(RES_STR['logging']['pub_bind'], address)
        self.pub_socket.bind(address)

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

    def get_handlers(self, signal: str) \
            -> List[Callable[[str, Coachbot, bytes],
                             Optional[NetworkResponses]]]:
        """Returns the handler for the given signal."""
        handlers = self._handlers.get(signal)
        return [] if handlers is None else handlers

    def exec_handler(self, signal: str, coachbot: Coachbot, message: bytes) \
            -> NetworkResponses:
        """Executes the handler for the given signal.

        Only the highest NetworkResponse is kept.
        """
        ret_val = NetworkResponses.SUCCESS
        for handler in self.get_handlers(signal):
            result = handler(signal, coachbot, message)
            if result is not None and result.value > ret_val.value:
                ret_val = result
        return ret_val

    def signal(self, sig_type: str, message: bytes) -> None:
        """This method sends out a signal to all coachbots listening (all
        booted ones).

        Parameters:
            sig_type (str): The signal name
            message (bytes): The data body to pass

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
        logging.debug(RES_STR['logging']['pub_signal'], sig_type)
        self.pub_socket.send(
            NetworkEventHandler.encode_signal_msg(sig_type, message))

    # pylint: disable=too-many-arguments
    def direct_signal(self, sig_type: str, coachbot: Coachbot,
                      message: bytes,
                      on_success: Callable[[NetStatus], None] = lambda _: None,
                      on_error: Callable[[NetStatus], None] = lambda _: None,
                      timeout: float = 2, max_retries: int = 5) -> None:
        """This method sends out a direct signal. Unlike the signal method,
        this method will give you informational info back on whether a signal
        was successfully handled.

        Parameters:
            sig_type (str): The signal name
            coachbot (Coachbot): The coachbot to send the signal to
            message (bytes): The data body to pass
            on_success (Callable[[NetStatus], None]): The callable called when
                a successful message is passed.
            on_error (Callable[[NetStatus], None]): The callable called when an
                error occurs.
            timeout: (float): The maximum timeout to wait for coachbots, total
            max_retries (int): The total number of tries to attempt before
                failing.

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
        self.req_socket.connect(_tcpurl(coachbot.address,
                                        get_coachswarm_net_req_port()))
        self.req_socket.send(
            NetworkEventHandler.encode_signal_msg(sig_type, message))

        retries_left = max_retries
        while retries_left > 0:
            if (self.req_socket.poll(timeout / max_retries) & zmq.POLLIN) != 0:
                result_raw = int(self.req_socket.recv())
                try:
                    result = NetStatus(result_raw)
                    return on_success(result)
                except ValueError:
                    # Building the NetStatus failed. Means we received a
                    # malfored response.
                    logging.warning(RES_STR['logging']['req_invalid_status'],
                                    result_raw)
                    return on_error(NetStatus.INVALID_RESPONSE)

            retries_left -= 1

        # If we don't get a response, let us simply close the socket.
        logging.warning(RES_STR['logging']['req_signal_timeout'])
        self.req_socket.setsockopt(zmq.LINGER, 0)
        self.req_socket.close()
        return on_error(NetStatus.TIMEOUT)

    def add_slot(
            self, sig_type: str,
            handler: Callable[[str, bytes], Optional[NetworkResponses]]) \
            -> None:
        """Registers a slot to handle the specified sig_type.

        Parameters:
            sig_type (str): The signal to be handled.
            handler (Callable[[str, Coachbot, bytes]]): The signal handler.
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

        sig = sig_bytes.rjust(NetworkEventHandler.SIGNAL_NAME_SIZE, b'\0')

        return base64.b64encode(sig + message)

    @staticmethod
    def decode_signal_msg(data: bytes) -> Tuple[str, Coachbot, bytes]:
        """Decodes a signal message into signal type and data.

        Parameters:
            data (bytes): The data

        Returns:
            Tuple[str, Coachbot, bytes]: The signal name, Coachbot that sent it
            and the message data
        """
        data_dec = base64.decodebytes(data)

        signal_b = \
            data_dec[:NetworkEventHandler.SIGNAL_NAME_SIZE].lstrip(b'\0')
        coachbot_id_b = \
            data_dec[NetworkEventHandler.SIGNAL_NAME_SIZE:
                     NetworkEventHandler.IDENTIFIER_SIZE].lstrip(b'\0')

        signal = signal_b.decode('ascii')
        coachbot_id = int(coachbot_id_b)
        message = data_dec[NetworkEventHandler.RECV_SIZE:]

        return signal, Coachbot(coachbot_id), message

    def tear_down(self) -> None:
        """Tears down the NetworkEventHandler. This is also hooked into
        __del__, so you don't necessarily need to call this manually."""
        self.worker.stop()

    def __del__(self):
        self.tear_down()
