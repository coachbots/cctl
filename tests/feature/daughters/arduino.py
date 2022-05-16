#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Holds the netutils unit test cases."""

import tempfile
import unittest
import os
import sys
from tests import async_test

sys.path.insert(0, os.path.abspath('./src'))

from cctl.daughters import arduino
from cctl import __VERSION__


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.5.1'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


class TestArduino(unittest.TestCase):
    """Tests whether the Arduino daughterboard is programmable and whether it
    is queriable for the version."""

    @async_test
    async def test_upload_force_no_err(self):
        """Ensures that the arduino script can be successfully uploaded."""
        await arduino.update(force=True)

    @async_test
    async def test_query_version(self):
        """Ensures that query version works after."""
        await arduino.update()
        version = await arduino.query_version()
        self.assertEqual(__VERSION__, version)

    @async_test
    async def test_charge_rail_set(self):
        """Ensures that it is possible to set the charge_rail power."""
        await arduino.update()
        await arduino.charge_rail_set(True)
        await arduino.charge_rail_set(False)


if __name__ == '__main__':
    unittest.main()
