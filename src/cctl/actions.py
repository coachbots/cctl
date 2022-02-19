# -*- coding: utf-8 -*-

"""Defines the main class that handles all commands."""

from typing import Callable, Iterable, Union, List
import re
from os import path
import logging
from argparse import Namespace
from subprocess import call
from multiprocessing import Process
import time

from cctl.res import ERROR_CODES, RES_STR
from cctl.api import camera_ctl, bot_ctl, configuration


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
        """Boots up the coachbot driver system.

        Todo:
            Shouldn't be implemented the way it is. Should be calling a
            module function.
        """
        def _start_ftp_server():
            call(['./cloud.py', configuration.get_server_interface()],
                 cwd=configuration.get_server_dir())

        def _start_manager():
            call(['./manager.py'], cwd=configuration.get_server_dir())

        ftp_server = Process(target=_start_ftp_server)
        coach_manager = Process(target=_start_manager)
        procs = [ftp_server, coach_manager]

        for proc in procs:
            proc.start()
            time.sleep(5)  # FIXME: Really bad

        for proc in procs:
            proc.join()

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
                    camera_ctl.make_processed_stream()

                    try:
                        camera_ctl.start_processing_stream()
                    except camera_ctl.CameraError:
                        logging.error(RES_STR['unknown_camera_error'])
                        return ERROR_CODES['unknown_camera_error']

            return 0
        if self._args.cam_command == RES_STR['cmd_cam_preview']:
            try:
                camera_ctl.start_processed_preview()
            except camera_ctl.CameraError:
                logging.error(RES_STR['unknown_camera_error'])
                return ERROR_CODES['unknown_camera_error']
            return 0

        return -1

    def _bot_id_handler(self,
            all_handler: Callable[[], int],
            some_handler: Callable[[List[bot_ctl.Coachbot]], int]) -> int:
        """This small method iterates through all bot-ids and runs handlers
        approperiately."""
        targets = []
        for identifier in self._args.id:
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

    def _start_pause_handler(self) -> int:
        target_on = self._args.command == RES_STR['cmd_start']
        target_str = RES_STR['cmd_start'] if target_on \
            else RES_STR['cmd_pause']

        logging.info(RES_STR['bot_operating_msg'], target_str)
        bot_ctl.set_user_code_running(target_on)
        return 0

    def _fetch_logs_handler(self):
        dump_dir = path.abspath(self._args.fetch_logs_directory) \
            if self._args.fetch_logs_directory else None

        if not isinstance(dump_dir, str):
            raise RuntimeError

        if self._args.fetch_logs_legacy:
            if not self._args.fetch_logs_directory:
                logging.error(RES_STR['fetch_logs_legacy_dir_not_specified'])
                return ERROR_CODES['malformed_cli_args']

            def _get_and_save_logs(bots: Iterable[bot_ctl.Coachbot]):
                def on_fetch(bot: bot_ctl.Coachbot, data: bytes):
                    dump_file = path.join(dump_dir, str(bot.identifier))
                    with open(dump_file, 'w+b') as m_file:
                        m_file.write(data)

                bot_ctl.fetch_legacy_logs(bots, on_fetch)

            def _all_handler() -> int:
                logging.info(RES_STR['fetch_logs_all_msg'], dump_dir)
                _get_and_save_logs(bot_ctl.get_all_coachbots())
                return 0

            def _some_handler(bots: Iterable[bot_ctl.Coachbot]) -> int:
                logging.info(RES_STR['fetch_logs_some_msg'],
                             ','.join(str(bot.identifier) for bot in bots),
                             dump_dir)
                _get_and_save_logs(bots)
                return 0

            return self._bot_id_handler(_all_handler, _some_handler)

        # TODO: Implement
        raise NotImplementedError

    def exec(self) -> int:
        """Parses arguments automatically and handles booting."""
        def _uploader():
            bot_ctl.upload_code(self._args.usr_path[0],
                                self._args.os_update)

        handlers = {
            'cam': self._camera_command_handler,
            RES_STR['cmd_on']: self._on_off_handler,
            RES_STR['cmd_off']: self._on_off_handler,
            RES_STR['cmd_blink']: self._blink_handler,
            RES_STR['cmd_fetch_logs']: self._fetch_logs_handler,
            RES_STR['cmd_start']: self._start_pause_handler,
            RES_STR['cmd_pause']: self._start_pause_handler,
            RES_STR['cmd_update']: _uploader,

            # TODO: make this a member method
            RES_STR['cmd_manage']: CommandAction.manage_system,
        }

        try:
            return handlers[self._args.command]

        except FileNotFoundError as fnf_err:
            logging.error(RES_STR['server_dir_missing'], fnf_err)
            return ERROR_CODES['server_dir_missing']
