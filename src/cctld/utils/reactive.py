#!/usr/bin/env python

"""Presents some convenience utilities for reactivex."""

import asyncio
from typing import Any, Callable
from reactivex.subject import BehaviorSubject


async def wait_until(subject: BehaviorSubject,
                     predicate: Callable[[Any], bool],
                     timeout: float = float('inf')) -> None:
    """This function blocks execution until ``predicate`` returns ``True`` on
    the given ``Observable``.
    """
    if predicate(subject.value):
        return

    event = asyncio.Event()

    def wrapper(value: Any):
        if predicate(value):
            event.set()

    subscription = subject.subscribe(on_next=wrapper)
    await event.wait()
    subscription.dispose()
