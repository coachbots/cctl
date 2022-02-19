# -*- coding: utf-8 -*-

"""This test suite runs the tests related to logging."""

import os
import sys
from cctl.api import configuration
from cctl.api.bot_ctl import boot_bots, fetch_legacy_logs

from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))

from cctl import netutils


class TestLogs(BotTestCase):
    """Tests whether the logging functions operate as expected."""
    def test_fetch_legacy_logs(self):
        """Tests whether legacy logs are fetched as expected."""
        test_bot = self.random_testing_bot
        test_bot.boot(True)
        expected_content = 'my_content\n\r'.encode('utf-8')
        netutils.write_remote_file(test_bot.address,
                                   configuration.get_legacy_log_file_path(),
                                   expected_content)
        actual_content = test_bot.fetch_legacy_log()
        self.assertEqual(expected_content, actual_content)

    def test_fetch_legacy_logs_throws_error_if_no_file(self):
        """Tests whether errors are thrown if legacy logs do not exist."""
        test_bot = self.random_testing_bot
        test_bot.boot(True)

        with netutils.sftp_client(test_bot.address) as client:
            try:
                client.remove(configuration.get_legacy_log_file_path())
            except IOError:
                pass

        with self.assertRaises(FileNotFoundError):
            test_bot.fetch_legacy_log()

    def test_fetch_multiple_legacy(self):
        """Tests whether it is possible to fetch multiple legacy logs."""
        boot_bots(self.test_bots, True)

        expected_contents = [f'my_content\n\r{bot.address}'.encode('utf-8')
                             for bot in self.test_bots]

        for bot, content in zip(self.test_bots, expected_contents):
            with netutils.sftp_client(bot.address) as client:
                client.remove(configuration.get_legacy_log_file_path())

            netutils.write_remote_file(
                bot.address, configuration.get_legacy_log_file_path(), content)

        logs = fetch_legacy_logs(self.test_bots)

        self.assertEqual(expected_contents, list(logs))
