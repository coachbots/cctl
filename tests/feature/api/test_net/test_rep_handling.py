# -*- coding: utf-8 -*-

import os
import tempfile
import textwrap
import sys

from zmq.error import ZMQError
from cctl.api.bot_ctl import Coachbot, boot_bots, set_user_code_running, upload_code

from cctl.api.network import Network
from cctl.network.net_status import NetStatus
from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))


class TestNetwork(BotTestCase):
    """Tests whether the network operates as expected."""

    def test_slot_works(self):
        """Tests whether a slot can be added for one bot."""

        target = self.random_testing_bot

        test_code = """
            def usr(robot):
                while True:
                    robot.net.cctl.signal('testsig', b'my_message')
                    robot.delay()
        """

        target.boot(True)

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

            def signal_handler(signal: str, bot: Coachbot, message: bytes):
                self.assertEqual(target, bot)
                self.assertEqual('testsig', signal)
                self.assertEqual(b'my_message', message)

            network = Network()
            try:
                network.user.add_slot('testsig', signal_handler)
                set_user_code_running(True)
            except ZMQError as zmqerr:
                self.fail(zmqerr)
            finally:
                network.tear_down()

    def test_slots_do_not_fail_if_order_is_weird(self):
        """Ensures that add_slot can be registered a bit later and still handle
        events."""
        target = self.random_testing_bot

        test_code = """
            def usr(robot):
                while True:
                    robot.net.cctl.signal('testsig', b'my_message')
                    robot.delay()
        """

        target.boot(True)

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)

            def signal_handler(signal: str, bot: Coachbot, message: bytes):
                self.assertEqual(target, bot)
                self.assertEqual('testsig', signal)
                self.assertEqual(b'my_message', message)

            network = Network()
            try:
                set_user_code_running(True)
                network.user.add_slot('testsig', signal_handler)
            except ZMQError as zmqerr:
                self.fail(zmqerr)
            finally:
                network.tear_down()
