#!/usr/bin/env python

import os
import sys
import random
import math
from compot.widgets import MainWindow, Column

sys.path.insert(0, os.path.abspath('./src'))

from cctl.models import Coachbot, CoachbotState, UserCodeState
from cctl.ui.coachbot_line import CoachbotLine
from cctl.utils.math import Vec2


if __name__ == '__main__':
    lines = []
    for i in range(100):
        bot = Coachbot(i, CoachbotState(
            is_on=random.choice([True, False]),
            os_version='1.2.0',
            bat_voltage=random.uniform(3, 4.2),
            position=Vec2(random.uniform(-5, 5), random.uniform(-10, 10)),
            theta=random.uniform(-math.pi, math.pi),
            user_code_state=UserCodeState(
                is_running=random.choice([True, False, None]),
                version=f'{random.randint(0, 80)}.'
                        f'{random.randint(0, 100)}.'
                        f'{random.randint(0, 100)}',
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
        lines.append(CoachbotLine(bot))

    events = MainWindow(Column(lines))
    events.subscribe()
