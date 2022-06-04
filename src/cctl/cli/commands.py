#!/usr/bin/env python

"""This module defines all the CLI commands that CCTL uses."""

import asyncio
from argparse import Namespace
from typing import List, Literal, Union
from reactivex import operators as rxops
from compot.widgets import ObserverMainWindow
from cctl.api.cctld import CCTLDClient, CCTLDCoachbotStateObservable
from cctl.models import Coachbot
from cctl.utils import parsers
from cctl.cli.command import cctl_command, cctl_command_group
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


@cctl_command('off')
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


@cctl_command('start')
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


@cctl_command('pause')
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
    raise NotImplementedError()


@cctl_command_group('cam')
async def cam_handler(args: Namespace, conf: Configuration) -> int:
    """Overhead Camera Control."""
    @cctl_command_group_element('preview')
    async def preview_handler(args: Namespace, conf: Configuration) -> int:
        """View the overhead video."""
        return 0

    @cctl_command_group_element('info')
    async def info_handler(args: Namespace, conf: Configuration) -> int:
        """Get Camera information."""
        return 0
