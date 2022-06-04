#!/usr/bin/env python

"""This package defines all endpoints that the request server is known to
handle. This is facilitated through the ``ENDPOINT_HANDLERS`` dictionary which
is buit upon the import of this module."""

import asyncio
import json
import logging
from typing import Any, Iterable, List, Tuple, Union
from cctl.models import Coachbot
from cctl.models.coachbot import CoachbotState
from cctl.protocols import ipc
from cctld.ble.errors import BLENotReachableError
from cctld.coach_commands import CoachCommand, CoachCommandError
from cctld.daughters import arduino
from cctld.models.app_state import AppState
from cctld.requests.handler import handler
from cctld.utils.reactive import wait_until


@handler(r'^/bots/state/?$', 'read')
async def read_bots_state(app_state: AppState, _, __) -> ipc.Response:
    """Returns the state of all the robots."""
    return ipc.Response(
        ipc.ResultCode.OK,
        json.dumps(
            [bots.to_dict() for bots in app_state.coachbot_states.value]
        )
    )


@handler(r'^/bots/state/is-on/?$', 'create')
async def create_bots_is_on(app_state: AppState, _: ipc.Request, __):
    """Turns all bots on."""
    off_bots = [Coachbot(i, state) for i, state
                in enumerate(app_state.coachbot_states.value)
                if not state.is_on]

    errs: List[BLENotReachableError] = []
    async for err in app_state.ble_manager.boot_bots(off_bots, True):
        errs.append(err)

    waiting_for = [bot for bot in off_bots
                   if bot not in [err.offender for err in errs]]
    await wait_until(app_state.coachbot_states,
                     lambda sts: all(sts[b].is_on for b in waiting_for))

    if len(errs) > 0:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT,
                            ' '.join([str(err) for err in errs]))
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/state/is-on/?$', 'delete')
async def delete_bots_is_on(app_state: AppState, _: ipc.Request, __):
    """Turns all bots off."""
    on_bots = [Coachbot(i, state) for i, state
               in enumerate(app_state.coachbot_states.value) if state.is_on]

    errs: List[BLENotReachableError] = []
    async for err in app_state.ble_manager.boot_bots(on_bots, False):
        errs.append(err)

    waiting_for = [bot for bot in on_bots
                   if bot not in [err.offender for err in errs]]
    await wait_until(app_state.coachbot_states,
                     lambda sts: all(not sts[b].is_on for b in waiting_for))

    if len(errs) > 0:
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT,
                            ' '.join([str(err) for err in errs]))
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/state/is-on/?$', 'create')
async def create_bot_is_on(
    app_state: AppState,
    _: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...],
):
    """Turns a bot on."""
    bot = Coachbot((ident := int(endpoint_groups[0])),
                   app_state.coachbot_states.value[ident])

    errors = []
    async for err in app_state.ble_manager.boot_bots([bot], True):
        errors.append(err)

    if len(errors) != 0:
        logging.getLogger('bluetooth').error('Could not turn bot %s on.',
                                             bot)
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(errors[0]))

    await wait_until(app_state.coachbot_states,
                     lambda states: states[bot.identifier].is_on)
    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/state/is-on/?$', 'delete')
async def delete_bot_is_on(
    app_state: AppState,
    _: ipc.Request,
    endpoint_groups: Tuple[Union[str, Any], ...]
):
    """Turns a bot off."""
    bot = Coachbot((ident := int(endpoint_groups[0])),
                   app_state.coachbot_states.value[ident])

    errors = []
    async for err in app_state.ble_manager.boot_bots([bot], False):
        errors.append(err)

    if len(errors) != 0:
        logging.getLogger('bluetooth').error('Could not turn bot %s on.',
                                             bot)
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(errors[0]))

    await wait_until(app_state.coachbot_states,
                     lambda states: not states[bot.identifier].is_on)
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


@handler(r'^/bots/user-code/running/?$', 'create')
async def create_bots_user_running(app_state: AppState, _, __):
    """Starts the user code for all running coachbots."""
    async def __boot_bot(bot: Coachbot):
        if not bot.state.is_on:
            return
        try:
            async with CoachCommand(
                bot.ip_address,
                app_state.config.coach_client.command_port
            ) as cmd:
                await cmd.set_user_code_running(True)
        except CoachCommandError as c_err:
            return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR,
                                str(c_err))

    errs = await asyncio.gather(
        *(__boot_bot(Coachbot(i, bot)) for i, bot in
          enumerate(app_state.coachbot_states.value)),
        return_exceptions=True)

    total_errors = [(i, err) for i, err in enumerate(errs) if err is not None]
    if len(total_errors) > 0:
        return ipc.Response(
            ipc.ResultCode.INTERNAL_SERVER_ERROR,
            f'Could not change bot states {total_errors}')

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/user-code/running/?$', 'delete')
async def delete_bots_user_running(app_state: AppState, _, __):
    """Stops the user code for all running coachbots."""
    async def __boot_bot(bot: Coachbot):
        if not bot.state.is_on:
            return
        try:
            async with CoachCommand(
                bot.ip_address,
                app_state.config.coach_client.command_port
            ) as cmd:
                await cmd.set_user_code_running(False)
        except CoachCommandError as c_err:
            return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR,
                                str(c_err))

    errs = await asyncio.gather(
        *(__boot_bot(Coachbot(i, bot)) for i, bot in
          enumerate(app_state.coachbot_states.value)),
        return_exceptions=True)

    total_errors = [(i, err) for i, err in enumerate(errs) if err is not None]
    if len(total_errors) > 0:
        return ipc.Response(
            ipc.ResultCode.INTERNAL_SERVER_ERROR,
            f'Could not change bot states {total_errors}')

    return ipc.Response(ipc.ResultCode.OK)


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


@handler(r'^/teapot/?$', 'read')
async def i_am_a_teapot(*args, **kwargs):
    """This function does not require documentation."""
    return ipc.Response(ipc.ResultCode.I_AM_A_TEAPOT)


@handler(r'^/rail/is-on/?$', 'create')
async def create_power_rail(app_state: AppState, *args, **kwargs):
    """Starts the power rail on."""
    try:
        await arduino.charge_rail_set(app_state.arduino_daughter, True)
        return ipc.Response(ipc.ResultCode.OK)
    except arduino.ArduinoError as aerr:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, str(aerr))


@handler(r'^/rail/is-on/?$', 'delete')
async def delete_power_rail(app_state: AppState, *args, **kwargs):
    """Starts the power rail on."""
    try:
        await arduino.charge_rail_set(app_state.arduino_daughter, False)
        return ipc.Response(ipc.ResultCode.OK)
    except arduino.ArduinoError as aerr:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, str(aerr))


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
