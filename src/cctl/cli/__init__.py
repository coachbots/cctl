#!/usr/bin/env python

"""This package exposes the CLI interface for cctl."""

import argparse
from argparse import ArgumentParser, Namespace
from cctl.conf import Configuration
from cctl.cli import commands

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.1.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

from cctl.cli.command import DECLARED_COMMANDS


def create_parser() -> ArgumentParser:
    """Given a parser, this function populates it with the declared commands
    and returns it."""
    parser = argparse.ArgumentParser(prog='cctl',
                                     description='Coachbot Control Utility')
    command_parser = parser.add_subparsers(title='command',
                                           help='Command A Robot',
                                           dest='command')
    for cmd in DECLARED_COMMANDS.values():
        mp = command_parser.add_parser(cmd.command_name, help=cmd.command_help)
        for arg in cmd.arguments:
            mp.add_argument(*arg[0], **arg[1])
    return parser


def exec_command(args: Namespace, conf: Configuration):
    """Executes the CLI command after it has been parsed. Returns the error
    code. Raises KeyError if the command does not exist."""
    return DECLARED_COMMANDS[args.command].handler(args, conf)
