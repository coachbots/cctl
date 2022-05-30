#!/usr/bin/env python

import asyncio
from typing import Awaitable, Callable


async def wait_until(predicate: Callable[[], Awaitable[bool]],
                     poll_interval: float) -> None:
    """Polls and waits until a predicate returns ``True``."""
    while True:
        if await predicate():
            return
        await asyncio.sleep(poll_interval)
