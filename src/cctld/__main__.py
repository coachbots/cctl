#!/usr/bin/env python

"""This is the main script that runs cctld."""

import asyncio
import logging
import sys
import os
from reactivex.subject.subject import Subject
from serial import SerialException

from cctl.models.coachbot import Coachbot, CoachbotState
from cctld import camera, daemon, servers
from cctld.ble import BleManager
from cctld.daughters.arduino import ArduinoInfo
from cctld.conf import Config
from cctld.models import AppState
from cctld.models.app_state import CoachbotStateSubject
from cctld.utils.net import host_is_reachable


async def auto_pruner(app_state: AppState):
    """The auto_pruner is a truly hacky way to automatically purge values that
    have possibly become stale from the ``coachbot_states``. How it works is
    that it basically goes through each robot in a loop, checking if they are
    currently awake and based on that setting them to ``None`` if they aren't.

    Todo:
        Really shouldn't need to exist, I feel like. Likely there is a better
        solution, but it's what we've got for now. This is not at all with what
        reactivex is about but I just don't know better for now.
    """
    async def __helper(bot_id, bot_state):
        bot = Coachbot(bot_id, bot_state)
        if not app_state.coachbot_states.get_subject(bot_id).value[1].is_on:
            return
        if not await host_is_reachable(bot.ip_address):
            logging.getLogger('auto-pruner').debug(
                'Could not reach %d. Pruning away.', bot_id)
            app_state.coachbot_states.get_subject(bot_id).on_next(
                (bot_id, CoachbotState(None)))

    while True:
        asyncio.gather(*(__helper(bot_id, bot_state)
                         for bot_id, bot_state in
                         app_state.coachbot_states.tuple_value),
                       return_exceptions=True)
        await asyncio.sleep(5)


async def __main(config: Config):
    """The main entry point of cctld."""
    app_state = AppState(
        coachbot_states=CoachbotStateSubject(
            tuple(CoachbotState(False) for _ in range(100))),
        coachbot_signals=Subject(),
        config=config,
        arduino_daughter=ArduinoInfo(
            config.arduino.executable,
            config.arduino.serial,
            config.arduino.baud_rate,
            config.arduino.board_type,
            os.path.join(config.general.workdir, 'arduino')
        ),
        camera_stream=camera.ProcessingStream(config),
        ble_manager=BleManager(config.bluetooth.interfaces)
    )

    try:
        await app_state.arduino_daughter.update(force=False)
    except (SerialException, OSError, RuntimeError):
        logging.getLogger('arduino').error(
            'Could not communicate with the Arduino. Continuing without the '
            'Arduino.')

    try:
        await app_state.camera_stream.start_stream()
    except RuntimeError:
        logging.getLogger('camera').error(
            'Could not start camera stream. No camera support is available.')

    logging.info('Initialization Done.')

    running_servers = asyncio.gather(
        servers.start_status_server(app_state),
        servers.start_ipc_request_server(app_state),
        servers.start_ipc_feed_server(app_state),
        servers.start_ipc_signal_forward_server(app_state),
        app_state.camera_stream.start_watchdog(),
        auto_pruner(app_state)
    )
    await running_servers


def main():
    """The main entry point of the program. This sets up logging and runs the
    program asynchronously."""
    config = Config()

    # Automatically create the workdir folder if it does not exist.
    if not os.path.exists(config.general.workdir):
        os.makedirs(config.general.workdir)

    # Set up the logging.
    logging.basicConfig(stream=sys.stderr, level=config.log.base)
    logging.getLogger('bleak').setLevel(logging.ERROR)
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('servers.request').setLevel(config.log.servers_request)
    logging.getLogger('servers.status').setLevel(config.log.servers_status)

    # Attempt to create the required directory for the IPC feeds. This may
    # fail. The admin is responsible for this anyways -- this simply minimizes
    # his headache.
    for paths in ((p := config.ipc).request_feed, p.state_feed, p.signal_feed):
        if paths.startswith('ipc://'):
            # TODO: Possibly buggy if a path contains ipc://
            directory = os.path.dirname(paths.replace('ipc://', ''))
            if not os.path.exists(directory):
                os.makedirs(directory)

    if __debug__:
        asyncio.run(__main(config))
    else:
        with daemon.context(config):
            asyncio.run(__main(config))


if __name__ == '__main__':
    main()
