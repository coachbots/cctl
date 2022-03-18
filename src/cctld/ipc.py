# -*- coding: utf-8 -*-

"""This module exposes all the inter-process communication that is to be used
with cctld.
"""

from cctl.api.bot_ctl import Coachbot


class IPCMessage:
    def __init__(self) -> None:
        pass


class IPCMessageState(IPCMessage):
    def __init__(self, bot: Coachbot, state: bool) -> None:
        super().__init__()
        self.bot = bot
        self.state = state
