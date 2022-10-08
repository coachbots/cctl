#!/usr/bin/env python

"""This package defines all endpoints that the request server is known to
handle. This is facilitated through the ``ENDPOINT_HANDLERS`` dictionary which
is buit upon the import of this module."""

import asyncio
import json
import logging
from serial import SerialException
from typing import Any, Tuple, Union
from cctl.models import Coachbot
from cctl.protocols import ipc
from cctld.coach_commands import CoachCommand, CoachCommandError
from cctld.models.app_state import AppState
from cctld.requests.handler import handler
from cctl.utils.color import hex_to_rgb
from cctld.utils.reactive import wait_until


@handler(r'^/bots/?$', 'read')
async def read_bots(app_state: AppState, _, __) -> ipc.Response:
    """Returns very basic information about the coachbots."""
    bot_states = app_state.coachbot_states.value
    return ipc.Response(
        ipc.ResultCode.OK,
        json.dumps([state.to_dict() for state in bot_states])
    )


@handler(r'^/bots/([0-9]+)/state/is-on/?$', 'create')
async def create_bot_is_on(
    app_state: AppState,
    req: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...],
):
    """Turns a bot on."""
    bot = Coachbot((ident := int(endpoint_groups[0])),
                   app_state.coachbot_states.value[ident])

    body = json.loads(req.body)
    if body.get('force') is None:
        return ipc.Response(ipc.ResultCode.BAD_REQUEST)

    if not body.get('force') and bot.state.is_on:
        return ipc.Response(ipc.ResultCode.OK)

    errors = []
    async for err in app_state.ble_manager.boot_bots([bot], True):
        errors.append(err)

    if len(errors) != 0:
        logging.getLogger('bluetooth').error('Could not turn bot %s on.', bot)
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(errors[0]))

    try:
        await wait_until(app_state.coachbot_states,
                        lambda states: states[bot.identifier].is_on,
                        app_state.config.constants.boot_timeout)
    except TimeoutError:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT,
                            'Network Layer Error')
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/state/is-on/?$', 'delete')
async def delete_bot_is_on(
    app_state: AppState,
    req: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...]
):
    """Turns a bot off."""
    bot = Coachbot((ident := int(endpoint_groups[0])),
                   app_state.coachbot_states.value[ident])

    body = json.loads(req.body)
    if body.get('force') is None:
        return ipc.Response(ipc.ResultCode.BAD_REQUEST)

    if not body.get('force') and not bot.state.is_on:
        return ipc.Response(ipc.ResultCode.OK)

    errors = []
    async for err in app_state.ble_manager.boot_bots([bot], False):
        errors.append(err)

    if len(errors) != 0:
        logging.getLogger('bluetooth').error('Could not turn bot %s on.',
                                             bot)
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(errors[0]))

    try:
        await wait_until(app_state.coachbot_states,
                         lambda states: not states[bot.identifier].is_on,
                         app_state.config.constants.boot_timeout)
    except TimeoutError:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT,
                            'Network Layer Error')
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
async def create_bot_user_running(app_state: AppState, _, endpoint_groups):
    """Starts the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if current_state.user_code_state.is_running:
        return ipc.Response(ipc.ResultCode.OK)

    try:
        async with CoachCommand(
            Coachbot(ident, current_state).ip_address,
                app_state.config.coach_client.command_port) as command:
            await command.set_user_code_running(True)
    except CoachCommandError as c_err:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR,
                            str(c_err))

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/user-code/running/?$', 'delete')
async def delete_bot_user_running(app_state: AppState, _, endpoint_groups):
    """Stops the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if not current_state.user_code_state.is_running:
        return ipc.Response(ipc.ResultCode.OK)

    try:
        async with CoachCommand(
            Coachbot(ident, current_state).ip_address,
                app_state.config.coach_client.command_port) as command:
            await command.set_user_code_running(False)
    except CoachCommandError as c_err:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR,
                            str(c_err))

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/user-code/code/?$', 'update')
async def update_bot_user_code(app_state: AppState, request: ipc.Request,
                               endpoint_groups):
    """Updates the user code."""
    ident = int(endpoint_groups[0])
    current_state = app_state.coachbot_states.value[ident]

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    if current_state.user_code_state.is_running:
        try:
            async with CoachCommand(
                Coachbot(ident, current_state).ip_address,
                    app_state.config.coach_client.command_port) as command:
                await command.set_user_code_running(False)
        except CoachCommandError as c_err:
            return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR,
                                str(c_err))

    try:
        async with CoachCommand(
            Coachbot(ident, current_state).ip_address,
                app_state.config.coach_client.command_port) as command:
            await command.set_user_code(request.body)
    except CoachCommandError as c_err:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR,
                            str(c_err))
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/led/color/?$', 'update')
async def update_bot_led_color(app_state: AppState, request: ipc.Request,
                               endpoint_groups) -> ipc.Response:
    """Updates the BOT LED color."""
    ident = int(endpoint_groups[0])
    color = request.body  # TODO: Convert to RGB tuple.
    current_state = app_state.coachbot_states.value[ident]

    try:
        color_t = hex_to_rgb(color)
    except RuntimeError:
        return ipc.Response(ipc.ResultCode.BAD_REQUEST)

    if not current_state.is_on:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

    async with CoachCommand(
        Coachbot(ident, current_state).ip_address,
            app_state.config.coach_client.command_port) as command:
        await command.set_led_color(color_t)

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/led/color/?$', 'update')
async def update_bots_led_color(app_state: AppState, request: ipc.Request,
                                _) -> ipc.Response:
    """Updates the bots LED color on all turned on bots."""
    on_bots = [Coachbot(i, state) for i, state
               in enumerate(app_state.coachbot_states.value) if state.is_on]

    color = request.body  # TODO: Convert to RGB tuple.

    async def set_bot_color(address: str):
        async with CoachCommand(
                address,
                app_state.config.coach_client.command_port) as command:
            await command.set_led_color(hex_to_rgb(color))

    await asyncio.gather(*[set_bot_color(bot.ip_address) for bot in on_bots])

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/teapot/?$', 'read')
async def i_am_a_teapot(*args, **kwargs):
    """This function does not require documentation."""
    return ipc.Response(ipc.ResultCode.I_AM_A_TEAPOT)


@handler(r'^/rail/is-on/?$', 'create')
async def create_power_rail(app_state: AppState, *args, **kwargs):
    """Starts the power rail on."""
    try:
        await app_state.arduino_daughter.charge_rail_set(True)
        return ipc.Response(ipc.ResultCode.OK)
    except SerialException as s_ex:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, str(s_ex))


@handler(r'^/rail/is-on/?$', 'delete')
async def delete_power_rail(app_state: AppState, *args, **kwargs):
    """Starts the power rail on."""
    try:
        await app_state.arduino_daughter.charge_rail_set(False)
        return ipc.Response(ipc.ResultCode.OK)
    except SerialException as s_ex:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, str(s_ex))


@handler(r'^/config/?$', 'read')
async def read_config(app_state: AppState, *args, **kwargs):
    """Returns configuration variables that may be of use to the cctl
    client."""
    return ipc.Response(ipc.ResultCode.OK, json.dumps({
        'feeds': {
            'request': app_state.config.ipc.request_feed,
            'state': app_state.config.ipc.state_feed,
            'signal': app_state.config.ipc.state_feed
        },
        'video': {
            'stream': app_state.config.video_stream.rtsp_host,
            'codec': app_state.config.video_stream.codec,
            'bitrate': app_state.config.video_stream.bitrate
        },
        'bluetooth': {
            'n_dongles': len(app_state.config.bluetooth.interfaces)
        }
    }))


@handler(r'^/info/video/?$', 'read')
async def read_info_video(app_state: AppState, *args, **kwargs):
    """Returns the endpoint info for video streaming."""
    host = app_state.config.video_stream.rtsp_host
    return ipc.Response(ipc.ResultCode.OK, json.dumps({
        'overhead-camera': {
            'enabled': app_state.config.video_stream.enabled,
            'endpoint': f'{host}/cctl/cam/overhead',
            'codec': app_state.config.video_stream.codec,
            'description': 'A H264 Stream of the Camera Above the Coachbots.'
        }
    }))
