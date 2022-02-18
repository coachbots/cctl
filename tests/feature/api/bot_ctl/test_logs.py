# -*- coding: utf-8 -*-

"""This test suite runs the tests related to logging."""

import os
import sys

from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))

from cctl import netutils


class TestLogs(BotTestCase):
    """Tests whether the logging functions operate as expected."""
    def setUp(self) -> None:
        super().setUp()
        self._test_bot = self.random_testing_bot
        self._test_bot.boot(True)

    def test_fetch_legacy_logs(self):
        """Tests whether legacy logs are fetched as expected."""
        expected_content = 'my_content\n\r'.encode('utf-8')
        netutils.write_remote_file(self._test_bot.address,
                                   '/home/hanlin/coach_os/experiment_log',
                                   expected_content)
        actual_content = self._test_bot.fetch_legacy_log()
        self.assertEqual(expected_content, actual_content)
