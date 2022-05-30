#!/usr/bin/env python

"""Presents some convenience utilities for reactivex."""

import asyncio
from typing import Any, Callable
import reactivex as rx


async def wait_until(observable: rx.Observable,
                     predicate: Callable[[Any], bool]) -> None:
    """This function blocks execution until ``predicate`` returns ``True`` on
    the given ``Observable``.
    """
    event = asyncio.Event()

    def wrapper(value: Any):
        if predicate(value):
            event.set()

    subscription = observable.subscribe(on_next=wrapper)
    await event.wait()
    subscription.dispose()
