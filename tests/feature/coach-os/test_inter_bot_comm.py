#!/usr/bin/env python

"""This test case runs tests that ensure that communication between all the
coachbots operates as expected."""

import asyncio
import sys
import os
from time import sleep, time
from cctl.api.bot_ctl import Coachbot
from tests.feature.bot_test_case import BotTestCase

sys.path.insert(0, os.path.abspath('./src'))
from cctl.api.network import Network

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.5.1'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


class TestInterBotComm(BotTestCase):
    """This test case asserts that the communication between bots in
        coach_os.custom_net operates exactly as expected.
    """

    def test_comms_reaches_1_to_1_64(self):
        """Tests whether communication between two bots works for 64 bytes."""
        message_count = 10
        timeout = 5

        sender, receiver = [self.test_bots[i] for i in range(2)]
        test_message = 'A' * 64

        sender_code = f"""
            def usr(bot):
                test_message = {test_message}
                for _ in range({message_count}):
                    bot.send_msg(test_message)
                    bot.delay()
                    bot.signal('send', chr(1))
        """

        receiver_code = f"""
            def usr(bot):
                test_message = {test_message}
                messages = bot.recv_msg()

                for msg in messages[:-{message_count}]:
                    bot.signal('recv', msg)
                    bot.delay()
        """
        sender.boot(True)
        receiver.boot(True)

        async def sender_uploader():
            await sender.async_upload_user_code(sender_code, False,
                                                usr_code_type_flag='s')

        async def receiver_uploader():
            await sender.async_upload_user_code(sender_code, False,
                                                usr_code_type_flag='s')

        asyncio.get_event_loop().run_until_complete(sender_uploader())
        asyncio.get_event_loop().run_until_complete(receiver_uploader())

        network = Network()

        sent, received = 0, 0

        def msg_sent_handler(_: str, __: Coachbot, value: bytes):
            nonlocal sent
            self.assertEqual(chr(1), value)
            sent += 1

        def msg_recv_handler(_: str, __: Coachbot, value: bytes):
            nonlocal received
            self.assertEqual(test_message, value.decode('ascii'))
            received += 1

        network.user.add_slot('send', msg_sent_handler)
        network.user.add_slot('recv', msg_recv_handler)

        start_time = time()
        while time() - start_time < timeout \
                and sent != message_count \
                and received != message_count:
            sleep(0.5)
