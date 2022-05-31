import contextlib
import asyncio


async def process_running(proc: asyncio.subprocess.Process):
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(proc.wait(), 1e-6)
    return proc.returncode is None
