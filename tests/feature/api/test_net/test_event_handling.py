# -*- coding: utf-8 -*-

import unittest
import os
import sys

from cctl.api.network import Network

sys.path.insert(0, os.path.abspath('./src'))


class TestNetwork(unittest.TestCase):
    """Tests functions pertaining to setting up the camera and the video stream
    successfully."""

    def test_event_handling(self):
        """Tests whether event handling operates as expected."""
        handler = Network()

        def _test_handler(_: str, message: bytes):
            self.assertEqual(b'test_message', message)

        handler.user.add_slot('test_signal_alpha', _test_handler)
