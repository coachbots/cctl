# -*- coding: utf-8 -*-

"""This module exports the network handler assigned to communicating with the
coachbots.
"""

import zmq

from cctl.netutils import get_ip_address
from cctl.api.configuration import get_coachswarm_net_user_port, \
    get_server_interface
from .base_handler import NetworkEventHandler


class UserNetworkEventHandler(NetworkEventHandler):
    """Represents a NetworkEventHandler that communicates with coachbots in
    user code.
    """

    def build_socket(self, zmq_ctx: zmq.Context) -> zmq.Socket:
        """Builds a socket to CCTL."""
        return zmq_ctx.socket(zmq.PUB)

    def connect_socket(self, socket: zmq.Socket):
        socket.bind('tcp://%s:%d' %
                    (get_ip_address(get_server_interface()),
                     get_coachswarm_net_user_port()))
