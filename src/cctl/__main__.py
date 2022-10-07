#!/usr/bin/env python3

import logging
import asyncio

from cctl.conf import Configuration

from cctl import cli


def main():
    """Main entry point of cctl."""
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(levelname)s]: %(message)s')
    logging.getLogger('asyncio').setLevel(logging.ERROR)

    conf = Configuration()

    parser = cli.create_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0

    return asyncio.run(cli.exec_command(args, conf))


if __name__ == '__main__':
    main()
