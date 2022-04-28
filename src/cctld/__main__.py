#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
from typing import Tuple
from cctl.models.coachbot import CoachbotState
import reactivex as rx
from dataclasses import dataclass
from cctld import daemon, servers


@dataclass
class AppState:
    bot_states: Tuple[CoachbotState, ...] = tuple(CoachbotState() for _ in
                                                  range(100))

async def main():
    """The main entry point of cctld."""
    state_subject = rx.subjects.BehaviorSubject(AppState())
    running_servers = asyncio.gather(
        servers.start_status_server(state_subject),
        servers.start_ipc_server(state_subject)
    )
    await running_servers


if __name__ == '__main__':
    if __debug__:
        asyncio.run(main())
    else:
        with daemon.context() as d_ctx:
            asyncio.run(main())
