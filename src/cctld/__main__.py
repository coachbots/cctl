#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
from contextlib import closing
import logging
import socket

from dataclasses import asdict, is_dataclass
from reactivex.subject import BehaviorSubject, Subject
from reactivex import Observer
from cctl.models.coachbot import CoachbotState, Coachbot
from cctld import daemon, servers
from cctld.models import AppState


class BotStateManager(Observer):
    """This class tracks changes in requested states and does its best to
    propagate those changes.

    This manager observes a ``Subject`` for ``Coachbot``s in it. As those
    ``Coachbot``s come in, the ``Coachbot.state`` field is read. For each
    non-null value in this, the ``BotStateManager`` will call the method of the
    same name as the field. Effectively, you can add more handlers for various
    fields by adding a method to this class of the same name as the field of
    the ``CoachbotState`` class.

    Todo:
        This class needs a significant rewrite since it is still adhering to a
        legacy API that is to be replaced.
    """
    def user_code_state_is_running(self, value: Coachbot, *args, **kwargs):
        """Changes the running user code to the target state as required.

        Todo:
            This is legacy.
        """
        my_ip = b'127.0.0.1'
        port = 5005
        broadcast_ip = 'localhost'
        config_bytes = b' '  # Dummy value, necessary for legacy protocol.
        assert value.state.user_code_state.is_running is not None
        target_op = b'START' if value.state.user_code_state.is_running \
            else b'STOP'
        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
            sock.sendto(target_op + b'_USR|' + config_bytes + b'|' + my_ip,
                        (broadcast_ip, port))

    def user_code_state_user_code(self, value: Coachbot, *args, **kwargs):
        """Updates the running user code to something new."""
        # TODO: Rewrite this. Actually, the user_code should contain metadata
        # information such as authorship and name of the file. This should be
        # built into a UserCodeState model which should then be uploaded rather
        # than sending this raw over the wire.
        port = 5005
        broadcast_ip = 'localhost'
        target_op = b'UPDATE'
        assert value.state.user_code_state.user_code is not None
        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
            sock.sendto(
                target_op + b'|' +
                value.state.user_code_state.user_code.encode(),
                (broadcast_ip, port)
            )


    def user_code_state(self, value: Coachbot, *args, **kwargs):
        """Handles user_code_state change requests."""
        self.__exec_handlers_for_dataclass(
            value.state.user_code_state, value, prefix='user_code_state')

    def _no_handler_for_field(self, *args, field: str, **kwargs):
        """Called when a handler function is not found for the field which has
        changed."""
        # TODO: Wrong logger
        logging.error('The handler for field %s does not exist.', field)

    def __exec_handlers_for_dataclass(self, obj, coachbot, prefix=''):
        for field, field_value in asdict(obj).items():
            if field_value is None:
                continue

            getattr(self, prefix + field,
                    self._no_handler_for_field)(coachbot, field=field)

    def on_next(self, value: Coachbot):
        # Iterate through all the new values we need to do on the coachbot.
        # If the field is None, means we don't need to touch it. If it is not
        # None, then we need to do something with it.
        self.__exec_handlers_for_dataclass(value.state, value)


async def __main():
    """The main entry point of cctld."""
    app_state = AppState(
        coachbot_states=BehaviorSubject(
            tuple(CoachbotState(False) for _ in range(100))),
        requested_states=Subject()
    )

    app_state.requested_states.subscribe(BotStateManager())

    running_servers = asyncio.gather(
        servers.start_status_server(app_state),
        servers.start_ipc_request_server(app_state),
        servers.start_ipc_feed_server(app_state),
    )
    await running_servers


def main():
    with daemon.context():
        asyncio.run(__main())


if __name__ == '__main__':
    main()
