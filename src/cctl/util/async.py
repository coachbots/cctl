#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Exposes design patterns."""

from asyncio import Lock
import functools

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.5.1'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


def uses_lock(lock: Lock):
    """This function can be used as a decorator to force an async lock call
    onto the decorated function."""
    def decorator(function):
        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            with await lock:
                return await function(*args, **kwargs)
        return wrapper
    return decorator
