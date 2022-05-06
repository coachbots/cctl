#!/usr/bin/env python

"""This package defines all endpoints that the request server is known to
handle. This is facilitated through the ``ENDPOINT_HANDLERS`` dictionary which
is buit upon the import of this module."""

import json
from typing import Any, Tuple, Union
from cctl.models import Coachbot
from cctl.protocols import ipc
from cctld.coach_btle_client import CoachbotBTLEClient, CoachbotBTLEError, \
    CoachbotBTLEStateException
from cctld.coach_commands import CoachCommand
from cctld.models.app_state import AppState
from cctld.requests.handler import handler


@handler(r'^/bots/state/?$', 'read')
async def read_bots_state(app_state: AppState, _, __) -> ipc.Response:
    """Returns the state of all the robots."""
    return ipc.Response(
        ipc.ResultCode.OK,
        json.dumps(bots.to_dict() for bots in app_state.coachbot_states.value))


@handler(r'^/bots/state/is-on/?$', 'create')
async def create_bot_is_on(
    app_state: AppState,
    _: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...]
):
    """Turns a bot on."""
    bot = Coachbot((ident := int(endpoint_groups[0])),
                   app_state.coachbot_states.value[ident])

    if bot.state.is_on:
        return ipc.Response(ipc.ResultCode.OK)

    async def boot_bot_on(client: CoachbotBTLEClient):
        try:
            await client.set_mode_led_on(True)
        except CoachbotBTLEStateException:
            await client.toggle_mode()
            await client.set_mode_led_on(True)

    try:
        await app_state.coachbot_btle_manager.execute_request(
            bot.bluetooth_mac_address, boot_bot_on)
    except CoachbotBTLEError as err:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(err))

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/state/is-on/?$', 'delete')
async def delete_bot_is_on(
    app_state: AppState,
    _: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...]
):
    """Turns a bot off."""
    bot = Coachbot((ident := int(endpoint_groups[0])),
                   app_state.coachbot_states.value[ident])

    if not bot.state.is_on:
        return ipc.Response(ipc.ResultCode.OK)

    async def boot_bot_off(client: CoachbotBTLEClient):
        try:
            await client.set_mode_led_on(False)
        except CoachbotBTLEStateException:
            await client.toggle_mode()
            await client.set_mode_led_on(False)

    try:
        await app_state.coachbot_btle_manager.execute_request(
            bot.bluetooth_mac_address, boot_bot_off)
    except CoachbotBTLEError as err:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(err))

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/state/?$', 'read')
async def read_bot_state(
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
async def create_bot_user_running(app_state, _, endpoint_groups):
    """Starts the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if current_state.user_code_running:
        return ipc.Response(ipc.ResultCode.OK)

    async with CoachCommand(
        Coachbot(ident, current_state).ip_address,
            app_state.config.coach_client.command_port) as command:
        await command.set_user_code_running(True)

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/user-code/running/?$', 'delete')
async def delete_bot_user_running(app_state, _, endpoint_groups):
    """Stops the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if not current_state.user_code_running:
        return ipc.Response(ipc.ResultCode.OK)

    async with CoachCommand(
        Coachbot(ident, current_state).ip_address,
            app_state.config.coach_client.command_port) as command:
        await command.set_user_code_running(False)

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/user-code/code/?$', 'update')
async def update_bot_user_code(app_state, request: ipc.Request,
                               endpoint_groups):
    """Updates the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if current_state.user_code_running:
        async with CoachCommand(
            Coachbot(ident, current_state).ip_address,
                app_state.config.coach_client.command_port) as command:
            await command.set_user_code_running(False)

    async with CoachCommand(
        Coachbot(ident, current_state).ip_address,
            app_state.config.coach_client.command_port) as command:
        await command.set_user_code(request.body)
    return ipc.Response(ipc.ResultCode.OK)


@handler('^/teapot', 'read')
async def i_am_a_teapot(*args, **kwargs):
    """This function does not require documentation."""
    return ipc.Response(ipc.ResultCode.I_AM_A_TEAPOT)
