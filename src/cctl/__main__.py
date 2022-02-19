#!/usr/bin/env python3

import argparse
import logging

from .res import RES_STR
from .actions import CommandAction


def main():
    """Main entry point of cctl."""
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(levelname)] :%(message)s')

    parser = argparse.ArgumentParser(prog=RES_STR['app_name'],
                                     description=RES_STR['app_desc'])

    command_parser = parser.add_subparsers(title=RES_STR['cmd_command'],
                                           help=RES_STR['cmd_command_help'],
                                           dest='command')
    on_parser = command_parser.add_parser(RES_STR['cmd_on'],
                                          help=RES_STR['cmd_on_help'])
    off_parser = command_parser.add_parser(RES_STR['cmd_off'],
                                           help=RES_STR['cmd_off_help'])
    blink_parser = command_parser.add_parser(RES_STR['cmd_blink'],
                                             help=RES_STR['cmd_blink_desc'])
    camera_parser = command_parser.add_parser(RES_STR['cmd_cam'],
                                              help=RES_STR['cmd_cam_desc'])
    command_parser.add_parser(RES_STR['cmd_start'],
                              help=RES_STR['cmd_start_desc'])
    command_parser.add_parser(RES_STR['cmd_pause'],
                              help=RES_STR['cmd_pause_desc'])
    update_parser = command_parser.add_parser(RES_STR['cmd_update'],
                                              help=RES_STR['cmd_update_desc'])
    command_parser.add_parser(RES_STR['cmd_manage'],
                              help=RES_STR['cmd_manage_desc'])

    for pars in (on_parser, off_parser, blink_parser):
        pars.add_argument(RES_STR['cmd_id'], metavar='N', type=str, nargs='+',
                          help=RES_STR['cmd_arg_id_help'])

    update_parser.add_argument('--operating-system', '-o',
                               help=RES_STR['cmd_update_os_desc'],
                               action='store_true', dest='os_update',
                               default=False)
    update_parser.add_argument('usr_path', metavar='PATH', type=str,
                               nargs=1, help=RES_STR['usr_code_path_desc'])

    fetch_logs_parser = command_parser.add_parser(
        RES_STR['cmd_fetch_logs'], help=RES_STR['cmd_fetch_logs_desc'])

    fetch_logs_parser.add_argument('--legacy', '-l', dest='fetch_logs_legacy',
                                   help=RES_STR['cmd_fetch_logs_legacy'])
    fetch_logs_parser.add_argument('--directory', '-d', nargs=1, type=str,
                                   dest='fetch_logs_directory',
                                   help=RES_STR['cmd_fetch_logs_directory'])

    cam_subparser = camera_parser.add_subparsers(
        title=RES_STR['cmd_cam_cmd_title'],
        help=RES_STR['cmd_cam_cmd_help'],
        dest='cam_command'
    )
    cam_subparser.add_parser(RES_STR['cmd_cam_setup'],
                             help=RES_STR['cmd_cam_setup_desc'])
    cam_subparser.add_parser(RES_STR['cmd_cam_preview'],
                             help=RES_STR['cmd_cam_preview_desc'])

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    return CommandAction(args).exec()
