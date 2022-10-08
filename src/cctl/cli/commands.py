#!/usr/bin/env python

"""This module defines all the CLI commands that CCTL uses."""

import os
import asyncio
from asyncio.subprocess import create_subprocess_exec
from argparse import Namespace
import sys
from typing import List, Literal, Optional, Tuple, Union
from collections import deque
import itertools
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
                'help': 'Target Robots. Format must be %%d, %%d-%%d or "all"'})


def _parse_arg_id(arg_ids: List[str]) -> Union[List[int], Literal['all']]:
    if len(arg_ids) > 1:
        return [int(arg) for arg in arg_ids]
    return parsers.iter_string(arg_ids[0])


def _output_errors_for_bots(
    grouped_bots: List[Tuple[Optional[CCTLDRespEx], List[Coachbot]]],
    op_msg: str
) -> None:
    total_cnt = sum((len(bots)
                    for bots in (group[1] for group in grouped_bots)))
    if len(grouped_bots) == 1 and grouped_bots[0][0] == None:
        print(f'Succeeded to {op_msg} {total_cnt}/{total_cnt} bots.',
              file=sys.stderr)
        return

    n_success = len(grouped_bots[0][1])
    if grouped_bots[0][0] == None:
        print(f'Succeeded to {op_msg} {n_success}/{total_cnt} bots.',
              file=sys.stderr)

    for error, bots in grouped_bots[1 if grouped_bots[0][0] == None else 0:]:
        n_fail = len(bots)
        print(f'Failed to {op_msg} {n_fail}/{total_cnt} bots due to {error}.',
              file=sys.stderr)

@cctl_command('on', arguments=[
    ARGUMENT_ID,
    (['-f', '--force'], {
        'help': 'Force sending BT commands regardless of bot state.',
        'action': 'store_true',
        'required': False
    })
])
async def on_handle(args: Namespace, config: Configuration) -> int:
    """Boot a range of robots up."""
    target_bots = [Coachbot.stateless(id) for id in range(100)] \
            if (t_arg := _parse_arg_id(args.id)) == 'all' \
            else [Coachbot.stateless(bot) for bot in t_arg]
    breakpoint()
    progress_queue_size = min(len(target_bots), 4)

    boot_queue = deque(target_bots)
    in_progress_queue = asyncio.Queue(progress_queue_size)

    for _ in range(progress_queue_size):
        in_progress_queue.put_nowait(boot_queue.pop())

    async def boot_bot(
        client: CCTLDClient,
    ) -> Tuple[Coachbot, Optional[CCTLDRespEx]]:
        bot = await in_progress_queue.get()
        try:
            await client.set_is_on(bot, True, force=args.force)

            if len(boot_queue) > 0:
                await in_progress_queue.put(boot_queue.pop())

            return (bot, None)
        except CCTLDRespEx as error:
            return (bot, error)

    async with CCTLDClient(config.cctld.request_host) as client:
        results = await asyncio.gather(*(
            boot_bot(client)
            for _ in range(len(target_bots))
        ))

    grouped_by_err = itertools.groupby(
            sorted(results, key=lambda x: x[1] or 0), lambda x: x[1])
    _output_errors_for_bots([(k, list(v)) for k, v in grouped_by_err],
                            'turn on')

    return 0


@cctl_command('off', arguments=[
    ARGUMENT_ID,
    (['-f', '--force'], {
        'help': 'Force sending BT commands regardless of bot state.',
        'action': 'store_true',
        'required': False
    })
])
async def off_handle(args: Namespace, config: Configuration) -> int:
    """Boot a range of robots down."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        target_bots = [Coachbot.stateless(id) for id in range(100)] \
                if targets == 'all' \
                else [Coachbot.stateless(bot) for bot in targets]

        await asyncio.gather(*(
            client.set_is_on(bot, False, force=args.force)
            for bot in target_bots
        ))
        return 0


@cctl_command('start', arguments=[ARGUMENT_ID])
async def start_handle(args: Namespace, config: Configuration) -> int:
    """Starts the user code on the specified coachbots."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        target_bots = [bot for bot in (Coachbot(i, state) for i, state in
                       enumerate(await client.read_all_states()))] \
                if targets == 'all' \
                else [Coachbot.stateless(bot) for bot in targets]

        await asyncio.gather(*(
            client.set_user_code_running(bot, True) for bot in target_bots))
        return 0


@cctl_command('pause', arguments=[ARGUMENT_ID])
async def pause_handle(args: Namespace, config: Configuration) -> int:
    """Stops the user code on the specified coachbots."""
    targets = _parse_arg_id(args.id)

    async with CCTLDClient(config.cctld.request_host) as client:
        target_bots = [bot for bot in (Coachbot(i, state) for i, state in
                       enumerate(await client.read_all_states()))] \
                if targets == 'all' \
                else [Coachbot.stateless(bot) for bot in targets]

        await asyncio.gather(*(
            client.set_user_code_running(bot, False) for bot in target_bots))
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
            target_bots = [bot for bot in (Coachbot(i, state) for i, state in
                           enumerate(await client.read_all_states()))] \
                    if targets == 'all' \
                    else [Coachbot.stateless(bot) for bot in targets]

            await asyncio.gather(*(
                client.set_led_color(bot, color_str) for bot in target_bots))
            return 0
    except CCTLDRespInvalidState as err_state:
        print(f'Error setting LED: {err_state}', file=sys.stderr)
        return 1
    except CCTLDRespBadRequest:
        print(f'{color_str} does not appear to be a valid color.',
              file=sys.stderr)
        return 1
