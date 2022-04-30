#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
from cctl.models.coachbot import CoachbotState
from reactivex.subject import BehaviorSubject
from cctld import daemon, servers
from cctld.models import AppState


async def main():
    """The main entry point of cctld."""
    app_state = AppState(
        coachbot_states=BehaviorSubject(
            (CoachbotState(False) for _ in range(100)))
    )

    running_servers = asyncio.gather(
        servers.start_status_server(app_state.coachbot_states),
        servers.start_ipc_request_server(app_state),
        servers.start_ipc_feed_server(app_state)
    )
    await running_servers


if __name__ == '__main__':
    if __debug__:
        asyncio.run(main())
    else:
        with daemon.context() as d_ctx:
            asyncio.run(main())
