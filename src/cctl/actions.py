# -*- coding: utf-8 -*-

"""Defines the main class that handles all commands."""

from typing import Union
import os
import shutil
import re
import logging
from argparse import Namespace
from subprocess import call
from multiprocessing import Process
import time

from cctl.res import ERROR_CODES, RES_STR
from cctl import camera_ctl, configuration

BotTargets = Union[range, bool]


def _parse_id(coach_id: str) -> BotTargets:
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
    """Class handling all actions that are supported by cctl. This class
    automatically parses arguments that argparse cannot and switches execution
    appropriately.
    """

    SERVER_DIR = configuration.get_server_dir()
    INTERFACE_NAME = configuration.get_server_interface()

    @staticmethod
    def boot_bot(bot_id: int, state: bool) -> None:
        """Changes the state of a bot to on or off.

        Parameters:
            bot_id - Target bot
            state - Whether to boot on or off

        FIXME:
            Shouldn't be implemented the way it is. Should be calling a module
            function.
        """
        call(['./ble_one.py', str(int(state)), str(bot_id)],
             cwd=CommandAction.SERVER_DIR)

    @staticmethod
    def boot_all(state: bool) -> None:
        """Turns all robots on or off.

        Parameters:
            state - Whether to boot on or off

        FIXME:
            Shouldn't be implemented the way it is. Should be calling a module
            function.
        """
        if state:
            call(['./reliable_ble_on.py'], cwd=CommandAction.SERVER_DIR)
            return

        call(['./reliable_ble_off.py'], cwd=CommandAction.SERVER_DIR)

    @staticmethod
    def set_operating(state: bool) -> None:
        """Turns user code on robots on or off.

        Parameters:
            state - Whether to unpause or pause

        FIXME:
            Shouldn't be implemented the way it is. Should be calling a module
            function.
        """
        if state:
            call(['./start.py'], cwd=CommandAction.SERVER_DIR)
            return

        call(['./stop.py'], cwd=CommandAction.SERVER_DIR)

    @staticmethod
    def blink(robot_id: int) -> None:
        """Blinks a robot.

        Parameters:
            bot_id - Target bot

        FIXME:
            Shouldn't be implemented the way it is. Should be calling a module
            function.
        """
        call(['./led_on.py', str(robot_id)], cwd=CommandAction.SERVER_DIR)

    @staticmethod
    def blink_all() -> None:
        """Blinks all robots.

        FIXME:
            - Shouldn't be implemented the way it is. Should be calling a
              module function.
            - Need to check whether bots are alive.
        """
        for i in range(0, 100):
            call(['./led_on.py', str(i)], cwd=CommandAction.SERVER_DIR)

    @staticmethod
    def manage_system() -> None:
        """Boots up the coachbot driver system.
        FIXME:
            - Shouldn't be implemented the way it is. Should be calling a
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

    @staticmethod
    def upload_code(usr_code: str, os_update: bool) -> None:
        """Uploads user code to all robots.

        Parameters:
            usr_code - The path to the target user code.

        FIXME:
            - Shouldn't be implemented the way it is. Should be calling a
              module function.
        """
        server_tmp = os.path.join(configuration.get_server_dir(), 'temp')

        shutil.copy2(usr_code, os.path.join(server_tmp, 'usr_code.py'))

        if not os_update:
            logging.info(RES_STR['upload_msg'])
            call(['./update.py', CommandAction.INTERFACE_NAME],
                 cwd=CommandAction.SERVER_DIR)
            return

        logging.info(RES_STR['upload_os_msg'])
        shutil.copy2(configuration.get_coachswarm_conf_path(),
                     os.path.join(server_tmp, 'coachswarm.conf'))
        # TODO: Remove these sleeps with a while loop.
        # TODO: I don't really know what this code does.
        call(['./scan.py'], cwd=CommandAction.SERVER_DIR)
        time.sleep(0.5)
        call(['./hard_push.py', CommandAction.INTERFACE_NAME],
             cwd=CommandAction.SERVER_DIR)
        time.sleep(0.5)
        call(['./reboot_batch.py', CommandAction.INTERFACE_NAME],
             cwd=CommandAction.SERVER_DIR)

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

    def exec(self) -> int:
        """Parses arguments automatically and handles booting."""
        try:
            if self._args.command == 'cam':
                return self._camera_command_handler()

            # Commands which contain ranges of robots.
            if self._args.command in (RES_STR['cmd_on'],
                                      RES_STR['cmd_off'],
                                      RES_STR['cmd_blink']):
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
                            CommandAction.boot_all(target_on)

                        if self._args.command == RES_STR['cmd_blink']:
                            logging.info(RES_STR['bot_all_blink_msg'])
                            CommandAction.blink_all()

                        break

                    # Else, go one-by-one turning robots on.
                    for bot in targets:
                        if self._args.command in (RES_STR['cmd_on'],
                                                  RES_STR['cmd_off']):
                            logging.info(RES_STR['bot_booting_msg'], bot,
                                         target_str)
                            CommandAction.boot_bot(bot, target_on)

                        if self._args.command == RES_STR['cmd_blink']:
                            logging.info(RES_STR['bot_blink_msg'], bot)
                            CommandAction.blink(bot)
                return 0

            # Start/Pause command.
            if self._args.command in (RES_STR['cmd_start'],
                                      RES_STR['cmd_pause']):
                target_on = self._args.command == RES_STR['cmd_start']
                target_str = RES_STR['cmd_start'] if target_on \
                    else RES_STR['cmd_pause']

                logging.info(RES_STR['bot_operating_msg'], target_str)
                CommandAction.set_operating(target_on)
                return 0

            # Upload command.
            if self._args.command == RES_STR['cmd_update']:
                CommandAction.upload_code(self._args.usr_path[0],
                                          self._args.os_update)
                return 0

            if self._args.command == RES_STR['cmd_manage']:
                CommandAction.manage_system()
                return 0

        except FileNotFoundError as fnf_err:
            logging.error(RES_STR['server_dir_missing'], fnf_err)
            return ERROR_CODES['server_dir_missing']

        return 0
