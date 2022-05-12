#!/usr/bin/env python

"""This package defines all endpoints that the request server is known to
handle. This is facilitated through the ``ENDPOINT_HANDLERS`` dictionary which
is buit upon the import of this module."""

import asyncio
import json
import logging
from typing import Any, Tuple, Union
from cctl.models import Coachbot
from cctl.protocols import ipc
from cctld.coach_btle_client import CoachbotBTLEClient, CoachbotBTLEError, CoachbotBTLEMode, \
    CoachbotBTLEStateException
from cctld.coach_commands import CoachCommand
from cctld.daughters import arduino
from cctld.models.app_state import AppState
from cctld.requests.handler import handler


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
    async def boot_bot_on(client: CoachbotBTLEClient):
        await client.set_mode(CoachbotBTLEMode.COMMAND)
        await client.set_mode_led_on(True)

    async def __helper(bot: Coachbot):
        if bot.state.is_on:
            return

        await app_state.coachbot_btle_manager.execute_request(
            bot.bluetooth_mac_address, boot_bot_on)

    errs = await asyncio.gather(*(__helper(Coachbot(i, state)) for i, state in
                                enumerate(app_state.coachbot_states.value)),
                                return_exceptions=True)
    if len([err for err in errs if err is not None]) > 0:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR)

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/state/is-on/?$', 'delete')
async def delete_bots_is_on(app_state: AppState, _: ipc.Request, __):
    """Turns all bots on."""
    async def boot_bot_off(client: CoachbotBTLEClient):
        await client.set_mode(CoachbotBTLEMode.COMMAND)
        await client.set_mode_led_on(False)

    async def __helper(bot: Coachbot):
        if bot.state.is_on:
            return

        await app_state.coachbot_btle_manager.execute_request(
            bot.bluetooth_mac_address, boot_bot_off)

    errs = await asyncio.gather(*(__helper(Coachbot(i, state)) for i, state in
                                enumerate(app_state.coachbot_states.value)),
                                return_exceptions=True)
    if len([err for err in errs if err is not None]) > 0:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR)

    return ipc.Response(ipc.ResultCode.OK)


@handler(r'^/bots/([0-9]+)/state/is-on/?$', 'create')
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
        await client.set_mode(CoachbotBTLEMode.COMMAND)
        await client.set_mode_led_on(True)

    try:
        await app_state.coachbot_btle_manager.execute_request(
            bot.bluetooth_mac_address, boot_bot_on)
    except CoachbotBTLEStateException as err:
        logging.getLogger('requests').error(
            'Could not change the state of bot %s due to %s', bot, err)
        return ipc.Response(ipc.ResultCode.STATE_CONFLICT, str(err))
    except CoachbotBTLEError as err:
        logging.getLogger('requests').error(
            'Could not change the state of bot %s due to %s', bot, err)
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR)

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

    if not bot.state.is_on:
        return ipc.Response(ipc.ResultCode.OK)

    async def boot_bot_off(client: CoachbotBTLEClient):
        await client.set_mode(CoachbotBTLEMode.COMMAND)
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


@handler(r'^/bots/user-code/running/?$', 'create')
async def create_bots_user_running(app_state: AppState, _, __):
    """Starts the user code for all running coachbots."""
    async def __boot_bot(bot: Coachbot):
        if bot.state.is_on:
            return
        async with CoachCommand(
            bot.ip_address,
            app_state.config.coach_client.command_port
        ) as cmd:
            await cmd.set_user_code_running(True)

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
        async with CoachCommand(
            bot.ip_address,
            app_state.config.coach_client.command_port
        ) as cmd:
            await cmd.set_user_code_running(False)

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
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, aerr)


@handler(r'^/rail/is-on/?$', 'delete')
async def delete_power_rail(app_state: AppState, *args, **kwargs):
    """Starts the power rail on."""
    try:
        await arduino.charge_rail_set(app_state.arduino_daughter, False)
        return ipc.Response(ipc.ResultCode.OK)
    except arduino.ArduinoError as aerr:
        return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, aerr)
