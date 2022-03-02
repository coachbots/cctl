# -*- coding: utf-8 -*-

import os
import tempfile
import textwrap
import sys

from zmq.error import ZMQError
from cctl.api.bot_ctl import boot_bots, set_user_code_running, upload_code

from cctl.api.network import Network
from cctl.network.net_status import NetStatus
from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))


class TestNetwork(BotTestCase):
    """Tests whether the network operates as expected."""

    def test_signal_transmits(self):
        """Tests whether a batch signal gets transmitted."""

        target_bots = self.test_bots[:2]

        test_code = """
            def usr(robot):
                def _handler(sig_type, message):
                    robot.net.cctl.signal('testsig', b'success')

                robot.net.cctl.add_slot('testsig', _handler)

                while True:
                    robot.delay()
        """

        boot_bots(target_bots, True)

        def back_handler(signal: str, message: bytes) -> None:
            self.assertEqual('testsig', signal)
            self.assertEqual(b'success', message)

        with tempfile.NamedTemporaryFile('w') as usr_file:
            usr_file.write(textwrap.dedent(test_code))
            usr_file.flush()

            upload_code(usr_file.name, False)
            set_user_code_running(True)

            network = Network()
            network.user.add_slot('testsig', back_handler)
            try:
                network.user.signal('testsig', b'')
            except ZMQError as zmqerr:
                self.fail(zmqerr)
            finally:
                network.tear_down()

    def test_signal_to_empty_gives_no_error(self):
        """Tests whether messaging no robots is completely fine."""

        network = Network()
        try:
            network.user.signal('testsig', b'some-message')
        except ZMQError as zmqerr:
            self.fail(zmqerr)
        finally:
            network.tear_down()
