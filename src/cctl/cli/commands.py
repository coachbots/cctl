#!/usr/bin/env python

"""This module defines all the CLI commands that CCTL uses."""

import os
import asyncio
from asyncio.subprocess import create_subprocess_exec
from argparse import Namespace
import sys
from typing import List, Literal, Union
from reactivex import operators as rxops
from compot.widgets import ObserverMainWindow
from cctl.api.cctld import CCTLDClient, CCTLDCoachbotStateObservable, \
    CCTLDRespBadRequest, CCTLDRespEx, CCTLDRespInvalidState
from cctl.models import Coachbot, CoachbotState
from cctl.utils import parsers
from cctl.cli.command import cctl_command
from cctl.conf import Configuration
from cctl.ui.manager import Manager

ARGUMENT_ID = (['id'],
               {'metavar': 'N', 'type': str, 'nargs': '+',
                'help': r'Target Robots. Format must be %d, %d-%d or "all"'})


def _parse_arg_id(arg_ids: List[str]) -> Union[List[int], Literal['all']]:
    if len(arg_ids) > 1:
        return [int(arg) for arg in arg_ids]
    return parsers.iter_string(arg_ids[0])


@cctl_command('on', arguments=[ARGUMENT_ID])
async def on_handle(args: Namespace, config: Configuration) -> int:
    """Boot a range of robots up."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        if targets == 'all':
            await client.set_is_on('all', True)
            return 0
        await asyncio.gather(*(
            client.set_is_on(Coachbot.stateless(bot), True)
            for bot in targets
        ))
        return 0


@cctl_command('off', arguments=[ARGUMENT_ID])
async def off_handle(args: Namespace, config: Configuration) -> int:
    """Boot a range of robots down."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        if targets == 'all':
            await client.set_is_on('all', False)
            return 0
        await asyncio.gather(*(
            client.set_is_on(Coachbot.stateless(bot), False)
            for bot in targets
        ))
        return 0


@cctl_command('start', arguments=[ARGUMENT_ID])
async def start_handle(args: Namespace, config: Configuration) -> int:
    """Starts the user code on the specified coachbots."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        if targets == 'all':
            await client.set_user_code_running('all', True)
            return 0
        await asyncio.gather(*(
            client.set_user_code_running(Coachbot.stateless(bot), True)
            for bot in targets
        ))
        return 0


@cctl_command('pause', arguments=[ARGUMENT_ID])
async def pause_handle(args: Namespace, config: Configuration) -> int:
    """Stops the user code on the specified coachbots."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        if targets == 'all':
            await client.set_user_code_running('all', False)
            return 0
        await asyncio.gather(*(
            client.set_user_code_running(Coachbot.stateless(bot), False)
            for bot in targets
        ))
        return 0


@cctl_command('manage')
async def manage_handle(_, conf: Configuration) -> int:
    """Spawns a management TUI."""
    data_stream, task = await CCTLDCoachbotStateObservable(
        conf.cctld.state_feed_host)
    try:
        ObserverMainWindow(
            Manager, data_stream.pipe(rxops.map(
                lambda sts: [Coachbot(i, st) for i, st in enumerate(sts)]))
        )
        await task
    except KeyboardInterrupt as key_int:
        data_stream.on_error(key_int)
        task.cancel()
    return 0


@cctl_command('update', arguments=[
    (['--operating-system', '-o'], {
        'dest': 'os_update', 'help': 'Also Update The Operating System',
        'action': 'store_true', 'default': False
    }),
    (['usr_path'], {
        'metavar': 'PATH', 'type': str, 'nargs': 1,
        'help': 'The path to the user code.'
    })
])
async def update_handler(args: Namespace, conf: Configuration) -> int:
    """Updates the code on all robots."""
    if args.os_update:
        raise NotImplementedError()

    with open(os.path.abspath(args.usr_path[0]), 'r') as source_f:
        source = source_f.read()

    async with CCTLDClient(conf.cctld.request_host) as client:
        res = await asyncio.gather(*(
            client.update_user_code(
                Coachbot(bot, CoachbotState(None)), source)
            for bot in range(100)),
            return_exceptions=True)
        print(res, file=sys.stderr)
        return 0


@cctl_command('cam.preview')
async def cam_preview_handler(args: Namespace, conf: Configuration) -> int:
    """Preview the video stream."""
    async with CCTLDClient(conf.cctld.request_host) as client:
        cam_info = (await client.get_video_info())['overhead-camera']

    proc = await create_subprocess_exec(
        *['ffplay', cam_info['endpoint']])
    await proc.communicate()
    return 0


@cctl_command('cam.info')
async def cam_info_handler(args: Namespace, conf: Configuration) -> int:
    """Presents you with helpful information on the video stream."""
    async with CCTLDClient(conf.cctld.request_host) as client:
        cam_info = (await client.get_video_info())['overhead-camera']

    print(f"Enabled\t\t{cam_info['enabled']}\n"
          f"Stream\t\t{cam_info['endpoint']}\n"
          f"Codec\t\t{cam_info['codec']}\n"
          f"Description\t{cam_info['description']}")
    return 0


@cctl_command('charger.on')
async def charger_on_handler(args: Namespace, conf: Configuration) -> int:
    """Turns on the rail."""
    async with CCTLDClient(conf.cctld.request_host) as client:
        try:
            await client.set_power_rail_on(True)
            return 0
        except CCTLDRespEx as ex:
            print(f'Could not change the charger state. The error is {ex}',
                  file=sys.stderr)
            return -1


@cctl_command('charger.off')
async def charger_off_handler(args: Namespace, conf: Configuration) -> int:
    """Turns off the rail."""
    async with CCTLDClient(conf.cctld.request_host) as client:
        try:
            await client.set_power_rail_on(False)
            return 0
        except CCTLDRespEx as ex:
            print(f'Could not change the charger state. The error is {ex}',
                  file=sys.stderr)
            return -1


@cctl_command(
    'led',
    arguments=[
        ARGUMENT_ID,
        (['--color', '-c'], {
            'dest': 'color',
            'help': 'Customize the color. Must be a HEX string (#ff0000)',
            'action': 'store', 'default': '#ff0000'
        })
    ]
)
async def led_handler(args: Namespace, conf: Configuration) -> int:
    """Sets the color of the LED."""
    targets = _parse_arg_id(args.id)
    color_str = str(args.color)

    try:
        async with CCTLDClient(conf.cctld.request_host) as client:
            if targets == 'all':
                await client.set_led_color('all', color_str)
                return 0
            await asyncio.gather(*(
                client.set_led_color(Coachbot.stateless(bot), color_str)
                for bot in targets
            ))
            return 0
    except CCTLDRespInvalidState as err_state:
        print(f'Error setting LED: {err_state}', file=sys.stderr)
        return 1
    except CCTLDRespBadRequest:
        print(f'{color_str} does not appear to be a valid color.',
              file=sys.stderr)
        return 2
