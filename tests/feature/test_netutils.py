#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Holds the netutils unit test cases."""

import tempfile
import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('./src'))

from cctl.api import configuration
from cctl import netutils


class TestNetutils(unittest.TestCase):
    """TestCase for the netutils."""
    def test_ping(self):
        """Tests whether ping works as expected."""
        self.assertEqual(0,
                         netutils.ping(netutils.get_ip_address(
                             configuration.get_server_interface())))

    def test_host_is_reachable(self):
        """Tests whether host_is_reachable works as expected."""
        self.assertTrue(netutils.host_is_reachable('localhost'))

    def test_read_remote_file(self):
        """Tests whether read_remote_file can read a remote file on
        localhost.

        This test operates by creating a temp file and reading it.
        """
        contents = 'Test File Contents\n\rTest File\n\r'.encode('utf-8')
        with tempfile.NamedTemporaryFile('w+b') as file:
            file.write(contents)
            file.flush()
            self.assertEqual(contents,
                             netutils.read_remote_file('localhost', file.name),
                             f'{file.name} did not have the correct contents.')


if __name__ == '__main__':
    unittest.main()
