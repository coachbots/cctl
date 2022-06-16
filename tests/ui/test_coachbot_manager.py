#!/usr/bin/env python

import os
import sys
import random
import math
from compot.widgets import MainWindow

sys.path.insert(0, os.path.abspath('./src'))

from cctl.models import Coachbot, CoachbotState, UserCodeState
from cctl.utils.math import Vec2
from cctl.ui.manager import Manager


if __name__ == '__main__':
    lines = []
    for i in range(100):
        bot = Coachbot(i, CoachbotState(
            is_on=random.choice([True, False]),
            os_version=random.choice(['1.2.0', None]),
            bat_voltage=random.choice([random.uniform(3, 4.2), None]),
            position=random.choice([
                Vec2(random.uniform(-5, 5), random.uniform(-10, 10)),
                None
            ]),
            theta=random.choice([
                random.uniform(-math.pi, math.pi),
                None
            ]),
            user_code_state=UserCodeState(
                is_running=random.choice([True, False, None]),
                version=random.choice([
                    f'{random.randint(0, 80)}.'
                    f'{random.randint(0, 100)}.'
                    f'{random.randint(0, 100)}',
                    None
                ]),
                name=random.choice([
                    'My Custom Test',
                    'Another Test',
                    None,
                    'Some Third Test',
                    'A Fourth Test I guess?',
                    'A really long test name that is way too long'
                ]),
                author=random.choice([
                    'Marko Vejnovic',
                    'Lin Liu',
                    'Billie Strong',
                    None
                ]),
                requires_version='1.0.0'
            )
        ))
        lines.append(bot)

    events = MainWindow(Manager(lines))
    events.subscribe()
