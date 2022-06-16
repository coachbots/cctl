import contextlib
import asyncio
from typing import Awaitable, Callable


async def process_running(proc: asyncio.subprocess.Process):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(proc.wait(), 1e-6)
    return proc.returncode is None


async def wait_until(predicate: Callable[[], Awaitable[bool]],
                     poll_interval: float) -> None:
    """Polls and waits until a predicate returns ``True``."""
    while True:
        if await predicate():
            return
        await asyncio.sleep(poll_interval)
