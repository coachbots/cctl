#!/usr/bin/env python

"""This package defines all endpoints that the request server is known to
handle. This is facilitated through the ``ENDPOINT_HANDLERS`` dictionary which
is buit upon the import of this module."""

from typing import Any, Dict, Tuple, Union
from dataclasses import replace
import re
from cctl.protocols import ipc
from cctld.models.app_state import AppState
from cctld.requests.handler import ENDPOINT_HANDLERS, IPCOperationT, \
    IPCReqHandlerT, handler


@handler(r'^/bots/([0-9]+)/state/?$', 'read')
def read_bot_state(
    app_state: AppState,
    _: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...]
) -> ipc.Response:
    """Returns the specific bot state."""
    return ipc.Response(
        ipc.ResultCode.OK,
        app_state.coachbot_states.value[int(endpoint_groups[1])]
    )


@handler(r'^/bots/([0-9]+)/user-code/running/?$', 'create')
def create_bot_user_running(app_state, _, endpoint_groups):
    """Starts the user code."""
    ident = int(endpoint_groups[1])
    (cb_states := app_state.coachbot_states).on_next(tuple(
        replace(state, user_code_running=True)
        if i == ident
        else state
        for i, state in enumerate(cb_states.value)
    ))
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/user-code/running/?$', 'delete')
def delete_bot_user_running(app_state, _, endpoint_groups):
    """Stops the user code."""
    ident = int(endpoint_groups[1])
    (cb_states := app_state.coachbot_states).on_next(tuple(
        replace(state, user_code_running=False)
        if i == ident
        else state
        for i, state in enumerate(cb_states.value)
    ))
    return ipc.Response(ipc.ResultCode.OK)
