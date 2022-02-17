# -*- coding: utf-8 -*-

"""Defines the main class that handles all commands."""

import asyncio
from typing import Union, Iterable
import re
import logging
from argparse import Namespace
from subprocess import call
from multiprocessing import Process
import time

from cctl.res import ERROR_CODES, RES_STR
from cctl.api import camera_ctl, bot_ctl, configuration


def _parse_id(coach_id: str) -> Union[range, bool]:
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
        return range(int(match.group(1)), int(match.group(2)) + 1)

    # Try matching with single:
    match = re.match(single_id_regex, coach_id)
    if match is not None:
        val = int(match.group(1))
        return range(val, val + 1)

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

    def _on_off_blink_handler(self) -> int:
        target_on = self._args.command == RES_STR['cmd_on']
        target_str = RES_STR['cmd_on'] if target_on \
            else RES_STR['cmd_off']

        for i in self._args.id:
            targets = _parse_id(i)

            # If one of the targets is a boolean, means we need to turn
            # on all.
            if isinstance(targets, bool):
                if self._args.command in (RES_STR['cmd_on'],
                                          RES_STR['cmd_off']):
                    logging.info(RES_STR['bot_all_booting_msg'],
                                 target_str)
                    bot_ctl.boot_bots('all', target_on)

                if self._args.command == RES_STR['cmd_blink']:
                    logging.info(RES_STR['bot_all_blink_msg'])
                    bot_ctl.blink('all')

                return 0

            if self._args.command in (RES_STR['cmd_on'], RES_STR['cmd_off']):
                bot_ctl.boot_bots((bot_ctl.Coachbot(i) for i in targets),
                                  target_on * len(targets))
                return 0

            for bot in targets:
                if self._args.command == RES_STR['cmd_blink']:
                    logging.info(RES_STR['bot_blink_msg'], bot)
                    bot_ctl.blink(bot)
        return 0

    def _start_pause_handler(self) -> int:
        target_on = self._args.command == RES_STR['cmd_start']
        target_str = RES_STR['cmd_start'] if target_on \
            else RES_STR['cmd_pause']

        logging.info(RES_STR['bot_operating_msg'], target_str)
        bot_ctl.set_user_code_running(target_on)
        return 0

    def exec(self) -> int:
        """Parses arguments automatically and handles booting."""
        try:
            if self._args.command == 'cam':
                return self._camera_command_handler()

            # Commands which contain ranges of robots.
            if self._args.command in (RES_STR['cmd_on'],
                                      RES_STR['cmd_off'],
                                      RES_STR['cmd_blink']):
                return self._on_off_blink_handler()

            # Start/Pause command.
            if self._args.command in (RES_STR['cmd_start'],
                                      RES_STR['cmd_pause']):
                return self._start_pause_handler()

            # Upload command.
            if self._args.command == RES_STR['cmd_update']:
                bot_ctl.upload_code(self._args.usr_path[0],
                                    self._args.os_update)
                return 0

            if self._args.command == RES_STR['cmd_manage']:
                CommandAction.manage_system()
                return 0

        except FileNotFoundError as fnf_err:
            logging.error(RES_STR['server_dir_missing'], fnf_err)
            return ERROR_CODES['server_dir_missing']

        return 0
