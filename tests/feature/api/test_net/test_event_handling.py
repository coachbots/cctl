# -*- coding: utf-8 -*-

import os
import tempfile
import textwrap
import sys

from zmq.error import ZMQError
from cctl.api.bot_ctl import upload_code

from cctl.api.network import Network
from cctl.network.net_status import NetStatus
from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))


class TestNetwork(BotTestCase):
    """Tests whether the network operates as expected."""

    def test_slot_success_status(self):
        """Tests whether bots can be directly messaged and whether they reply
        correctly for a correct status."""

        target_bot = self.random_testing_bot
        target_bot.boot(True)

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    return robot.net.results.SUCCESS
                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        def on_success(status: NetStatus):
            self.assertTrue(NetStatus.SUCCESS, status)

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

            try:
                network = Network()
                network.user.direct_signal('testsig', target_bot, b'',
                                           on_success=on_success)
            except ZMQError as zmqerr:
                self.fail(zmqerr)

    def test_direct_signal_invalid_status(self):
        """Tests whether coachbots can be messaged directly and whether an
        invalid status is raised if they return an invalid result code."""

        target_bot = self.random_testing_bot
        target_bot.boot(True)

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    return robot.net.results.INVALID_RESPONSE
                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        def on_error(status: NetStatus):
            self.assertTrue(NetStatus.INVALID_RESPONSE, status)

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

            try:
                network = Network()
                network.user.direct_signal('testsig', target_bot, b'',
                                           on_error=on_error)
            except ZMQError as zmqerr:
                self.fail(zmqerr)
