#!/usr/bin/env python

import asyncio
import time
from typing import Awaitable, Callable


async def wait_until(predicate: Callable[[], Awaitable[bool]],
                     poll_interval: float = 0.2,
                     timeout: float = float('inf')) -> None:
    """Polls and waits until a predicate returns ``True``.

    If the timeout parameter is specified, this function will raise a
    TimeoutError.

    Parameters:
        predicate (Callable[[], Awaitable[bool]]): The predicate to test.
        poll_interval (float): The amount of time to wait between polls.
            Default 0.2s
        timeout (float): The amount of time to wait before raising
            TimeoutError.
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if await predicate():
            return
        await asyncio.sleep(poll_interval)
    raise TimeoutError()
