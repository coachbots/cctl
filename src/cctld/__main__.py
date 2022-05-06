#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
from reactivex.subject import BehaviorSubject
from reactivex.subject.subject import Subject

from cctld.coach_btle_client import CoachbotBTLEClientManager
from cctl.models.coachbot import CoachbotState
from cctld import daemon, servers
from cctld.conf import Config
from cctld.models import AppState


async def __main():
    """The main entry point of cctld."""
    config = Config()
    app_state = AppState(
        coachbot_states=BehaviorSubject(
            tuple(CoachbotState(False) for _ in range(100))),
        coachbot_signals=Subject(),
        config=config,
        coachbot_btle_manager=CoachbotBTLEClientManager(
            config.bluetooth.interfaces)
    )

    running_servers = asyncio.gather(
        servers.start_status_server(app_state),
        servers.start_ipc_request_server(app_state),
        servers.start_ipc_feed_server(app_state),
        servers.start_ipc_signal_forward_server(app_state)
    )
    await running_servers


def main():
    with daemon.context():
        asyncio.run(__main())


if __name__ == '__main__':
    main()
