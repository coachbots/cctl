#!/usr/bin/env python

"""This package defines all endpoints that the request server is known to
handle. This is facilitated through the ``ENDPOINT_HANDLERS`` dictionary which
is buit upon the import of this module."""

from typing import Any, Tuple, Union
from cctl.models import Coachbot
from cctl.models.coachbot import CoachbotState
from cctl.protocols import ipc
from cctld.models.app_state import AppState
from cctld.requests.handler import handler


@handler(r'^/bots/([0-9]+)/state/?$', 'read')
def read_bot_state(
    app_state: AppState,
    _: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...]
) -> ipc.Response:
    """Returns the specific bot state."""
    return ipc.Response(
        ipc.ResultCode.OK,
        app_state.coachbot_states.value[int(endpoint_groups[0])].serialize()
    )


@handler(r'^/bots/([0-9]+)/user-code/running/?$', 'create')
def create_bot_user_running(app_state, _, endpoint_groups):
    """Starts the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if current_state.user_code_running:
        return ipc.Response(ipc.ResultCode.OK)

    app_state.requested_states.on_next(
        Coachbot(ident, CoachbotState(user_code_running=True)))
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/user-code/running/?$', 'delete')
def delete_bot_user_running(app_state, _, endpoint_groups):
    """Stops the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if not current_state.user_code_running:
        return ipc.Response(ipc.ResultCode.OK)

    app_state.requested_states.on_next(
        Coachbot(ident, CoachbotState(user_code_running=False)))
    return ipc.Response(ipc.ResultCode.OK)


@handler('^/teapot', 'read')
def i_am_a_teapot(*args, **kwargs):
    """This function does not require documentation."""
    return ipc.Response(ipc.ResultCode.I_AM_A_TEAPOT)
