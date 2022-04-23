#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
from cctld import daemon, servers


async def main():
    """The main entry point of cctld."""
    running_servers = asyncio.gather(
        servers.start_management_server()
    )
    await running_servers


if __name__ == '__main__':
    with daemon.context():
        asyncio.run(main())
