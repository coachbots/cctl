#!/usr/bin/env python3

import argparse
import logging

from .res import RES_STR
from .actions import CommandAction


def main():
    """Main entry point of cctl."""
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(levelname)s]: %(message)s')

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

    fetch_logs_parser = command_parser.add_parser(
        RES_STR['cmd_fetch_logs'], help=RES_STR['cmd_fetch_logs_desc'])

    fetch_logs_parser.add_argument('--legacy', '-l', dest='fetch_logs_legacy',
                                   action='store_true',
                                   help=RES_STR['cmd_fetch_logs_legacy'])
    fetch_logs_parser.add_argument('--directory', '-d', nargs=1, type=str,
                                   dest='fetch_logs_directory',
                                   help=RES_STR['cmd_fetch_logs_directory'])

    for pars in (on_parser, off_parser, blink_parser, fetch_logs_parser):
        pars.add_argument(RES_STR['cmd_id'], metavar='N', type=str, nargs='+',
                          help=RES_STR['cmd_arg_id_help'])

    update_parser.add_argument('--operating-system', '-o',
                               help=RES_STR['cmd_update_os_desc'],
                               action='store_true', dest='os_update',
                               default=False)
    update_parser.add_argument('usr_path', metavar='PATH', type=str,
                               nargs=1, help=RES_STR['usr_code_path_desc'])

    cam_subparser = camera_parser.add_subparsers(
        title=RES_STR['cmd_cam_cmd_title'],
        help=RES_STR['cmd_cam_cmd_help'],
        dest='cam_command'
    )
    cam_subparser.add_parser(RES_STR['cmd_cam_setup'],
                             help=RES_STR['cmd_cam_setup_desc'])
    cam_subparser.add_parser(RES_STR['cmd_cam_preview'],
                             help=RES_STR['cmd_cam_preview_desc'])

    exec_parser = command_parser.add_parser(
        RES_STR['cli']['exec']['name'], help=RES_STR['cli']['exec']['help'])
    exec_parser.add_argument(
        RES_STR['cli']['exec']['bots']['name'],
        help=RES_STR['cli']['exec']['bots']['help'],
        metavar=RES_STR['cli']['exec']['bots']['metavar'],
        nargs=1
    )
    exec_parser.add_argument(
        RES_STR['cli']['exec']['command']['name'],
        help=RES_STR['cli']['exec']['command']['help'],
        metavar=RES_STR['cli']['exec']['command']['metavar'],
        nargs='+'
    )
    exec_parser.add_argument(
        RES_STR['cli']['exec']['proxy']['name'],
        help=RES_STR['cli']['exec']['proxy']['help'],
        action='store_true'
    )

    install_parser = command_parser.add_parser(
        RES_STR['cli']['install']['name'],
        help=RES_STR['cli']['install']['help']
    )
    install_parser.add_argument(
        RES_STR['cli']['install']['bots']['name'],
        help=RES_STR['cli']['install']['bots']['help'],
        metavar=RES_STR['cli']['install']['bots']['metavar'],
        nargs=1
    )
    install_parser.add_argument(
        RES_STR['cli']['install']['packages']['name'],
        help=RES_STR['cli']['install']['packages']['help'],
        metavar=RES_STR['cli']['install']['packages']['metavar'],
        nargs='+'
    )

    charger_parser = command_parser.add_parser(
        RES_STR['cli']['charger']['name'],
        help=RES_STR['cli']['charger']['help']
    )
    charger_parser.add_argument(
        RES_STR['cli']['charger']['state']['name'],
        help=RES_STR['cli']['charger']['state']['help'],
        metavar=RES_STR['cli']['charger']['state']['metavar'],
        nargs=1
    )

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    return CommandAction(args).exec()


if __name__ == '__main__':
    main()
