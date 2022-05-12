#!/usr/bin/env python

"""This module exposes small network-related utilities."""

import asyncio


async def ping(hostname: str, count: int = 1,
               max_timeout: float = 1) -> int:
    """Asynchronously pings a hostname.

    Parameters:
        hostname (str): The target to ping
        count (int): The number of times to ping it.
        max_timeout (float): The maximum number of seconds before ping gives
            up.

    Returns:
        int: The ping status code.
    """
    return await (await asyncio.create_subprocess_exec(
        'ping',
        '-c', str(count),
        '-w', str(max_timeout),
        hostname,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )).wait()


async def host_is_reachable(hostname: str,
                            max_attempts: int = 1) -> bool:
    """Asynchronously checks whether a host is reachable via ping.

    Parameters:
        hostname (str): The target to ping.
        max_attempts (int): The maximum number attempts you are willing to
            ping.

    Returns:
        bool: Whether the host was reachable on any attempt.
    """
    for _ in range(max_attempts):
        if (await ping(hostname, 1)) == 0:
            return True
    return False
