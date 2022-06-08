#!/usr/bin/env python

"""Declares the utility decorator used for declaring commands and creates a new
translation unit for holding declared commands."""

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Any, Tuple
from argparse import Namespace
import functools
from cctl.conf import Configuration
from cctl.utils.datastructures import Tree

DECLARED_COMMANDS: Dict[str, 'CCTLCommandHandler'] = {}

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
                 arguments: ArgT = []):
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
        DECLARED_COMMANDS[name] = CCTLCommandHandler(
            name,
            helps if helps is not None else function.__doc__,
            function,
            arguments
        )
        return wrapper
    return decorator
