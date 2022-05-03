#!/usr/bin/env python

from typing import Iterable

from cctl.models.coachbot import Coachbot

from compot.composable import Composable
from compot.widgets import Column
from cctl.ui.coachbot_line import CoachbotLine


@Composable
def Manager(state: Iterable[Coachbot], *args, **kwargs):
    return Column([CoachbotLine(b) for b in state], *args, **kwargs)
