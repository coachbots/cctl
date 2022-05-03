# -*- coding: utf-8 -*-

"""Defines the main class that handles all commands."""

import sys
import asyncio
from typing import Callable, Iterable, Union, List
import re
from os import path
import os
import logging
from compot.widgets import ObserverMainWindow
from argparse import Namespace
from reactivex import operators as rxops
import serial
from cctl.api.cctld import CCTLDCoachbotStateObservable
from cctl.models.coachbot import Coachbot
from cctl.ui.manager import Manager
from cctl.utils.net import sftp_client

from cctl.res import ERROR_CODES, RES_STR
from cctl.api import camera_ctl, bot_ctl, charge_ctl, configuration


def _parse_id(coach_id: str) -> Union[List[int], bool]:
    """Parses the id parameter ensuring that it fits the format:
        ^(\\d+)$ or ^(\\d+)-(\\d+)$. If 'all' is given, then the function
        returns true, otherwise returns a list of targets to be turned on.
    """
    single_id_regex = r'^(\d+)$'
    range_regex = r'^(\d+)-(\d+)$'

    if coach_id == 'all':
        return True

    # Try matching with range first:
    match = re.match(range_regex, coach_id)
    if match is not None:
        return list(range(int(match.group(1)), int(match.group(2)) + 1))

    # Try matching with single:
    match = re.match(single_id_regex, coach_id)
    if match is not None:
        val = int(match.group(1))
        return list(range(val, val + 1))

    raise AttributeError(RES_STR['unsupported_argument'])


class CommandAction:
    """
    Class handling all actions that are supported by cctl. This class
    automatically parses arguments that argparse cannot and switches execution
    appropriately.
    """

    @staticmethod
    def manage_system() -> None:
        """Starts the UI that displays the management information of the
        coachbots.

        Todo:
            A hack implementation since ``cctl`` isn't fully asyncio ready yet.
        """

        async def __helper():
            data_stream, task = await CCTLDCoachbotStateObservable(
                configuration.get_state_feed())

            ObserverMainWindow(
                Manager, data_stream.pipe(rxops.map(
                    lambda sts: [Coachbot(i, st) for i, st in enumerate(sts)]))
            )
            await task

        asyncio.get_event_loop().run_until_complete(__helper())

    def __init__(self, args: Namespace):
        self._args = args

    def _camera_command_handler(self) -> int:
        """Handles camera commands.

        Note:
            This function may exit prematurely using sys.exit if something
            fails. This is expected behavior.

        Returns:
            0 for a successful invokation, -1 otherwise.
        """
        if self._args.cam_command == RES_STR['cmd_cam_setup']:
            try:
                camera_ctl.start_processing_stream()
            except camera_ctl.CameraError as v_err:
                if v_err.identifier == camera_ctl.CameraEnum.CAMERA_RAW.value:
                    logging.error(RES_STR['camera_raw_error'])
                    return ERROR_CODES['camera_raw_error']

                if v_err.identifier == \
                        camera_ctl.CameraEnum.CAMERA_CORRECTED.value:
                    logging.info(RES_STR['camera_stream_does_not_exist'])
                    try:
                        camera_ctl.make_processed_stream()
                    except camera_ctl.CameraError:
                        return ERROR_CODES['processed_stream_creating_error']

                    try:
                        camera_ctl.start_processing_stream()
                    except camera_ctl.CameraError:
                        logging.error(RES_STR['unknown_camera_error'])
                        return ERROR_CODES['unknown_camera_error']
            except FileExistsError:
                pass

            return 0
        if self._args.cam_command == RES_STR['cmd_cam_preview']:
            try:
                camera_ctl.start_processed_preview()
            except camera_ctl.CameraError:
                logging.error(RES_STR['unknown_camera_error'])
                return ERROR_CODES['unknown_camera_error']
            return 0

        return -1

    def _bot_id_handler(
            self,
            all_handler: Callable[[], int],
            some_handler: Callable[[List[bot_ctl.Coachbot]], int],
            identifiers=None) -> int:
        """This small method iterates through all bot-ids and runs handlers
        approperiately."""
        targets = []
        target_ids = identifiers if identifiers is not None else self._args.id
        for identifier in target_ids:
            parsed = _parse_id(identifier)

            if isinstance(parsed, bool):
                return all_handler()

            targets += [bot_ctl.Coachbot(bot_id) for bot_id in parsed]

        return some_handler(targets)

    def _on_off_handler(self) -> int:
        target_on = self._args.command == RES_STR['cmd_on']
        target_str = RES_STR['cmd_on'] if target_on \
            else RES_STR['cmd_off']

        def _all_handler() -> int:
            logging.info(RES_STR['bot_all_booting_msg'],
                         target_str)
            bot_ctl.boot_bots('all', target_on)
            return 0

        def _some_handler(bots: Iterable[bot_ctl.Coachbot]) -> int:
            logging.info(RES_STR['bot_booting_many_msg'],
                         ','.join([str(bot.identifier) for bot in bots]),
                         target_str)
            bot_ctl.boot_bots(bots, target_on)
            return 0

        return self._bot_id_handler(_all_handler, _some_handler)

    def _blink_handler(self) -> int:
        def _all_handler() -> int:
            logging.info(RES_STR['bot_all_blink_msg'])
            bot_ctl.blink('all')
            return 0

        def _some_handler(bots: Iterable[bot_ctl.Coachbot]) -> int:
            logging.info(RES_STR['bot_blink_many_msg'],
                         ','.join([str(bot.identifier) for bot in bots]))
            bot_ctl.blink_bots(bots)
            return 0

        return self._bot_id_handler(_all_handler, _some_handler)

    def run_command_handler(self) -> int:
        """Handles the case of cctl exec.

        Returns:
            The exit code.
        """
        command = ' '.join(self._args.exec_command)
        bots = self._args.bots[0].split(',')
        prox_port = configuration.get_socks5_port() if self._args.proxy else -1

        def _some_handler(bots: List[bot_ctl.Coachbot]) -> int:
            for bot in bots:
                with bot.run_ssh(command, prox_port) as conn:
                    _, stdout, stderr = conn
                    print(stdout.read().decode())
                    print(stderr.read().decode(), file=sys.stderr)
                    stdout.channel.recv_exit_status()
            return 0

        return self._bot_id_handler(
            lambda: _some_handler(bot_ctl.get_alives()), _some_handler, bots)

    def install_packages_handler(self) -> int:
        """Handles the case of 'cctl install packages'

        Returns:
            The exit code.
        """
        packages = self._args.install_packages
        bots = self._args.bots[0].split(',')
        prox_port = configuration.get_socks5_port()

        pip_cmd_fmt = f'echo {configuration.get_pi_password()} | sudo -S ' + \
            'pip install %s ' + \
            f'--proxy socks5:127.0.0.1:{configuration.get_socks5_port()}'

        def _some_handler(bots: List[bot_ctl.Coachbot]) -> int:
            for bot in bots:
                for package in packages:
                    full_path = path.abspath(package)
                    if path.exists(full_path):
                        pkg_name = path.basename(full_path)
                        remote_path = f'/tmp/{pkg_name}'
                        with sftp_client(bot.address) as client:
                            client.put(full_path, remote_path)
                            with bot.run_ssh(pip_cmd_fmt % (remote_path),
                                             prox_port) as conn:
                                _, sout, serr = conn
                                print(sout.read().decode())
                                print(serr.read().decode(), file=sys.stderr)
                                sout.channel.recv_exit_status()
                                continue

                    with bot.run_ssh(pip_cmd_fmt % (package),
                                     prox_port) as conn:
                        _, stdout, stderr = conn
                        print(stdout.read().decode())
                        print(stderr.read().decode(), file=sys.stderr)
                        stdout.channel.recv_exit_status()
            return 0

        return self._bot_id_handler(
            lambda: _some_handler(bot_ctl.get_alives()), _some_handler, bots)

    def _start_pause_handler(self) -> int:
        target_on = self._args.command == RES_STR['cmd_start']
        target_str = RES_STR['cmd_start'] if target_on \
            else RES_STR['cmd_pause']

        logging.info(RES_STR['bot_operating_msg'], target_str)
        bot_ctl.set_user_code_running(target_on)
        return 0

    def _fetch_logs_handler(self):
        dump_dir = path.abspath(self._args.fetch_logs_directory[0]) \
            if self._args.fetch_logs_directory else None

        if self._args.fetch_logs_legacy:
            if not dump_dir:
                logging.error(RES_STR['fetch_logs_legacy_dir_not_specified'])
                return ERROR_CODES['malformed_cli_args']

            def _get_and_save_logs(bots: Iterable[bot_ctl.Coachbot],
                                   dump_dir: str):
                def on_fetch(bot: bot_ctl.Coachbot, data: bytes):
                    dump_file = path.join(dump_dir, str(bot.identifier))
                    with open(dump_file, 'w+b') as m_file:
                        m_file.write(data)

                if not path.isdir(dump_dir):
                    os.mkdir(dump_dir)

                bot_ctl.fetch_legacy_logs(bots, on_fetch)

            def _all_handler() -> int:
                logging.info(RES_STR['fetch_logs_all_msg'], dump_dir)
                _get_and_save_logs(bot_ctl.get_all_coachbots(), dump_dir)
                return 0

            def _some_handler(bots: Iterable[bot_ctl.Coachbot]) -> int:
                logging.info(RES_STR['fetch_logs_some_msg'],
                             ','.join(str(bot.identifier) for bot in bots),
                             dump_dir)
                _get_and_save_logs(bots, dump_dir)
                return 0

            return self._bot_id_handler(_all_handler, _some_handler)

        # TODO: Implement
        raise NotImplementedError

    def charger_on_off_handler(self) -> int:
        """Controls whether the charger should be turned on or off."""
        state = bool(self._args.state == 'on')
        try:
            asyncio.get_event_loop().run_until_complete(
                charge_ctl.charge_rail_set(state))
        except serial.SerialException as sex:
            logging.error(RES_STR['arduino_comm_err'], sex)
            return ERROR_CODES['daughterboard_comm_issue']
        except RuntimeError as rex:
            logging.error(rex)
            return ERROR_CODES['daughterboard_comm_issue']
        return 0

    def exec(self) -> int:
        """Parses arguments automatically and handles booting."""
        def _uploader():
            bot_ctl.upload_code(self._args.usr_path[0],
                                self._args.os_update)

        handlers = {
            RES_STR['cmd_cam']: self._camera_command_handler,
            RES_STR['cmd_on']: self._on_off_handler,
            RES_STR['cmd_off']: self._on_off_handler,
            RES_STR['cmd_blink']: self._blink_handler,
            RES_STR['cmd_fetch_logs']: self._fetch_logs_handler,
            RES_STR['cmd_start']: self._start_pause_handler,
            RES_STR['cmd_pause']: self._start_pause_handler,
            RES_STR['cmd_update']: _uploader,
            RES_STR['cli']['exec']['name']: self.run_command_handler,
            RES_STR['cli']['install']['name']: self.install_packages_handler,
            RES_STR['cli']['charger']['name']: self.charger_on_off_handler,

            # TODO: make this a member method
            'manage': CommandAction.manage_system,
        }

        try:
            return handlers[self._args.command]()

        except FileNotFoundError as fnf_err:
            logging.error(RES_STR['server_dir_missing'], fnf_err)
            return ERROR_CODES['server_dir_missing']
