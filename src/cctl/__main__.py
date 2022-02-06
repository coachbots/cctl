#!/usr/bin/env python3

import sys
import argparse
import logging

from .res import RES_STR
from .actions import CommandAction


def main():
    """Main entry point of cctl."""
    logging.basicConfig(level=logging.DEBUG)

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
    start_parser = command_parser.add_parser(RES_STR['cmd_start'],
                                             help=RES_STR['cmd_start_desc'])
    pause_parser = command_parser.add_parser(RES_STR['cmd_pause'],
                                             help=RES_STR['cmd_pause_desc'])
    update_parser = command_parser.add_parser(RES_STR['cmd_update'],
                                              help=RES_STR['cmd_update_desc'])

    for p in (on_parser, off_parser, blink_parser):
        p.add_argument(RES_STR['cmd_id'], metavar='N', type=str, nargs='+',
                       help=RES_STR['cmd_arg_id_help'])

    update_parser.add_argument('--operating-system', '-o',
                               help=RES_STR['cmd_update_os_desc'],
                               action='store_true', dest='os_update',
                               default=False)
    update_parser.add_argument('usr_path', metavar='PATH', type=str,
                               nargs=1, help=RES_STR['usr_code_path_desc'])

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    return CommandAction(args).exec()
