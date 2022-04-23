#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
from cctld import daemon, servers


async def main():
    """The main entry point of cctld."""
    running_servers = asyncio.gather(
        servers.start_management_server(),
        servers.start_ipc_server()
    )
    await running_servers


if __name__ == '__main__':
    asyncio.run(main())
