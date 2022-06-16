#!/usr/bin/env python

"""Declares the utility decorator used for declaring commands and creates a new
translation unit for holding declared commands."""

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Any, Tuple
from argparse import Namespace
import functools
from cctl.conf import Configuration

DECLARED_COMMANDS: Dict[str, Any] = {}

ArgT = Iterable[Tuple[List[str], Dict[str, Any]]]


@dataclass
class CCTLCommandHandler:
    """Represents a command handler."""
    command_name: str
    command_help: str
    handler: Callable[[Namespace, Configuration], int]
    arguments: ArgT = field(default_factory=lambda: [])


def cctl_command(name: str,
                 helps: Optional[str] = None,
                 arguments: ArgT = tuple()):
    """A decorator that creates the appropriate argparse subparsers and
    handlers.

    You can use this decorator to create custom commands:

    .. example::

       @cctl_command('cam.preview')
       async def cam_preview_handler(args, conf) -> int:
           print('Called when cam.preview')
           return 0
    """
    def decorator(function):
        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            return await function(*args, **kwargs)

        subparsers = name.split('.')
        pointer = DECLARED_COMMANDS
        while len(subparsers) > 1:
            parser = subparsers[0]
            if pointer.get(parser) is None:
                pointer[parser] = {}
            subparsers = subparsers[1:]
            pointer = DECLARED_COMMANDS[parser]

        pointer[subparsers[0]] = CCTLCommandHandler(
            subparsers[0],
            helps if helps is not None else function.__doc__,
            function,
            arguments
        )
        return wrapper
    return decorator
