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
import os


async def __main(config: Config):
    """The main entry point of cctld."""
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
    config = Config()

    # Automatically create the workdir folder if it does not exist.
    if not os.path.exists(config.general.workdir):
        os.makedirs(config.general.workdir)

    # Attempt to create the required directory for the IPC feeds. This may
    # fail. The admin is responsible for this anyways -- this simply minimizes
    # his headache.
    for paths in ((p := config.ipc).request_feed, p.state_feed, p.signal_feed):
        directory = os.path.dirname(paths)
        if not os.path.exists(directory):
            os.makedirs(directory)

    if __debug__:
        asyncio.run(__main(config))
    else:
        with daemon.context(config):
            asyncio.run(__main(config))


if __name__ == '__main__':
    main()
