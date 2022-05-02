#!/usr/bin/env python

"""This module defines the ``handler`` decorator which registeres handlers in
``ENDPOINT_HANDLERS``, a variable from which the IPC Request server then
reads."""

from typing import Callable, Dict, Tuple, Union, Any
from typing_extensions import Literal
import re
from cctl.protocols import ipc
from cctld.models.app_state import AppState

IPCReqHandlerT = Callable[[AppState, ipc.Request, Tuple[Union[str, Any], ...]],
                          ipc.Response]
IPCOperationT = str


ENDPOINT_HANDLERS: Dict[str, Dict[IPCOperationT, Callable]] = {}


def handler(endpoint_regex: str,
            operation: Literal['create', 'read', 'update', 'delete']):
    """The handler decorator registers your endpoint handler for a given IPC
    request operation.

    For example:

    .. code-block:: python

       from cctld.models import AppState
       from cctl.protocols import ipc

       @handler('^/bots/state/?$', 'read')
       def all_bots_state_read(app_state: AppState, request: ipc.Request,
                               regex_matches):
           return ipc.Response(ipc.ResultCode.OK,
                               app_state.coachbot_states.value)
    """
    def factory(function: IPCReqHandlerT):
        if ENDPOINT_HANDLERS.get(endpoint_regex) is None:
            ENDPOINT_HANDLERS[endpoint_regex] = {}
        ENDPOINT_HANDLERS[endpoint_regex][operation] = function

        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper
    return factory


def get(
    endpoint: str,
    method: IPCOperationT
) -> Tuple[IPCReqHandlerT, Tuple[Union[str, Any], ...]]:
    """Returns a handler for a specific endpoint and method.

    Raises:
        ValueError: If the specified endpoint does not exist.
        KeyError: If the method is not supported for the specified endpoint.
    """
    for endpoint_regex, handlers in ENDPOINT_HANDLERS.items():
        match = re.match(endpoint_regex, endpoint)
        if not match:
            continue

        return (handlers[method], match.groups())

    raise ValueError(f'The endpoint {endpoint} could not be found.')
