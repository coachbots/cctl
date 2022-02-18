# -*- coding: utf-8 -*-

"""This test suite runs the tests related to logging."""

import os
import sys
import uuid
from cctl.api import configuration

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
                                   configuration.get_legacy_log_file_path(),
                                   expected_content)
        actual_content = self._test_bot.fetch_legacy_log()
        self.assertEqual(expected_content, actual_content)

    def test_fetch_legacy_logs_throws_error_if_no_file(self):
        """Tests whether errors are thrown if legacy logs do not exist."""
        temp_old_exp_path = '/tmp/' + str(uuid.uuid4())[:8]
        need_to_restore_backup = False

        with netutils.sftp_client(self._test_bot.address) as client:
            try:
                client.rename(configuration.get_legacy_log_file_path(),
                              temp_old_exp_path)
                need_to_restore_backup = True
            except IOError:
                pass

        with self.assertRaises(FileNotFoundError):
            self._test_bot.fetch_legacy_log()

        if need_to_restore_backup:
            with netutils.sftp_client(self._test_bot.address) as client:
                client.rename(temp_old_exp_path,
                              configuration.get_legacy_log_file_path())
