#!/usr/bin/env python3

import logging
import asyncio

from cctl.conf import Configuration

from cctl import cli


def main():
    """Main entry point of cctl."""
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(levelname)s]: %(message)s')

    conf = Configuration()

    parser = cli.create_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    return asyncio.run(cli.exec_command(args, conf))

    """
    blink_parser = command_parser.add_parser(RES_STR['cmd_blink'],
                                             help=RES_STR['cmd_blink_desc'])
    camera_parser = command_parser.add_parser(
        'cam', help='Overhead Camera Control')
    update_parser = command_parser.add_parser(RES_STR['cmd_update'],
                                              help=RES_STR['cmd_update_desc'])

    fetch_logs_parser = command_parser.add_parser(
        RES_STR['cmd_fetch_logs'], help=RES_STR['cmd_fetch_logs_desc'])

    fetch_logs_parser.add_argument('--legacy', '-l', dest='fetch_logs_legacy',
                                   action='store_true',
                                   help=RES_STR['cmd_fetch_logs_legacy'])
    fetch_logs_parser.add_argument('--directory', '-d', nargs=1, type=str,
                                   dest='fetch_logs_directory',
                                   help=RES_STR['cmd_fetch_logs_directory'])

    cam_subparser = camera_parser.add_subparsers(
        title='camera-command',
        help='Camera Command',
        dest='cam_command'
    )
    cam_subparser.add_parser(
        'info', help='Displays information about the camera stream.')
    cam_subparser.add_parser('preview', help='Previews the overhead camera.')

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
    """


if __name__ == '__main__':
    main()
