# -*- coding: utf-8 -*-

import os
import tempfile
import textwrap
import sys
from cctl.api.bot_ctl import upload_code

from cctl.api.network import Network
from cctl.network.net_status import NetStatus
from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))


class TestNetwork(BotTestCase):
    """Tests whether the network operates as expected."""

    def test_direct_signal_success_status(self):
        """Tests whether coachbots can be messaged directly and whether they
        reply to signals as expected."""

        target_bot = self.random_testing_bot
        target_bot.boot(True)

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    return 0
                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        def on_success(status: NetStatus):
            self.assertTrue(NetStatus.SUCCESS, status)

        with tempfile.TemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

            network = Network()
            network.user.direct_signal('testsig', target_bot, b'',
                                       on_success=on_success)

    def test_direct_signal_invalid_status(self):
        """Tests whether coachbots can be messaged directly and whether they
        reply to signals as expected."""

        target_bot = self.random_testing_bot
        target_bot.boot(True)

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    return 15
                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        def on_error(status: NetStatus):
            self.assertTrue(NetStatus.INVALID_RESPONSE, status)

        with tempfile.TemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

            network = Network()
            network.user.direct_signal('testsig', target_bot, b'',
                                       on_error=on_error)
