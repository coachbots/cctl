# -*- coding: utf-8 -*-

import os
import tempfile
import textwrap
import sys
from time import sleep

sys.path.insert(0, os.path.abspath('./src'))

from zmq.error import ZMQError
from cctl.api.bot_ctl import set_user_code_running, upload_code

from cctl.api.network import Network
from cctl.network.net_status import NetStatus
from tests.feature.bot_test_case import BotTestCase


class TestNetwork(BotTestCase):
    """Tests whether the network operates as expected."""

    def test_direct_signal_success_status(self):
        """Tests whether bots reply for a success."""

        target_bot = self.random_testing_bot
        target_bot.boot(True)

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    robot.logger.info('(signal=%s, message=%s) -> %s' %
                                      (sig_type, message,
                                      robot.net.results.SUCCESS))
                    return robot.net.results.SUCCESS
                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        on_success_called = False

        def on_success(status: NetStatus):
            nonlocal on_success_called
            on_success_called = True
            self.assertEqual(NetStatus.SUCCESS, status)

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()
            upload_code(usr_file.name, False)

        network = Network()

        set_user_code_running(False)
        set_user_code_running(True)
        sleep(2)  # Wait for the server to actually start.

        try:
            network.user.direct_signal('testsig', target_bot, b'',
                                       on_success=on_success)
            sleep(2)  # Wait for two seconds for on_success to fire.
        except ZMQError as zmqerr:
            self.fail(zmqerr)
        finally:
            network.tear_down()

        self.assertTrue(on_success_called)

    def test_direct_signal_invalid_status(self):
        """Tests whether bots raise invalid status on an invalid result"""

        target_bot = self.random_testing_bot
        target_bot.boot(True)

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    robot.logger.info('(signal=%s, message=%s) -> %s' %
                                      (sig_type, message,
                                      robot.net.results.INVALID_RESPONSE))
                    return robot.net.results.INVALID_RESPONSE
                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        on_error_called = False

        def on_error(status: NetStatus):
            nonlocal on_error_called
            on_error_called = True
            self.assertTrue(NetStatus.INVALID_RESPONSE, status)

        def on_success(status: NetStatus):
            self.fail(f'on_success called with result: {status}')

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

        network = Network()
        set_user_code_running(True)
        sleep(2)

        try:
            network.user.direct_signal('testsig', target_bot, b'',
                                       on_success=on_success,
                                       on_error=on_error)
            sleep(2)
        except ZMQError as zmqerr:
            self.fail(zmqerr)
        finally:
            network.tear_down()

        self.assertTrue(on_error_called)

    def test_direct_signal_timeout(self):
        """Tests whether an unreachable coachbot does not crash anything."""

        target_bot = self.random_testing_bot
        target_bot.boot(False)

        on_error_called = False

        def on_error(status: NetStatus):
            nonlocal on_error_called
            on_error_called = True
            self.assertEqual(NetStatus.TIMEOUT, status)

        network = Network()
        sleep(2)

        try:
            network.user.direct_signal('testsig', target_bot, b'',
                                       on_error=on_error)
            sleep(2)
        except ZMQError as zmqerr:
            self.fail(zmqerr)
        finally:
            network.tear_down()

        self.assertTrue(on_error_called)
