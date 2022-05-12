#!/usr/bin/env python

import math

from compot import ColorPairs, LayoutSpec, MeasurementSpec, LayoutSpec
from compot.composable import Composable
from compot.widgets import Row, RowSpacing, Text, TextStyleSpec, ProgressBar


from cctl.models import Coachbot, UserCodeState

@Composable
def UserInfo(user_info: UserCodeState):
    """The ``UserInfo`` widget displays information about the currently running
    user code."""
    MAX_NAME_LEN = 24
    MAX_AUTHOR_LEN = 16
    VERSION_LEN = 10

    run_str, run_color = \
        ('❔ Unknown', ColorPairs.WARNING_INVERTED) \
            if (r := user_info.is_running) is None \
            else (
                ('🦾 Running ', ColorPairs.OK_INVERTED) if r \
                else ('💀 Stopped', ColorPairs.ERROR_INVERTED))
    version_str = str(v if (v := user_info.version) is not None else '?.?.?')
    name_str = (n[:MAX_NAME_LEN - 3] + '...' if len(n) > MAX_NAME_LEN
                else n) \
        if (n := user_info.name) is not None else 'Unknown Name'
    author_str = (a[:MAX_AUTHOR_LEN - 3] + '...' if len(a) > MAX_AUTHOR_LEN
                  else a) \
        if (a := user_info.author) is not None else 'Unknown Author'

    return Row(
        (
            Text(f' {run_str} ', style=TextStyleSpec(color=run_color)),
            Text(f' {name_str.ljust(MAX_NAME_LEN)}▕'),
            Text(f' {author_str.ljust(MAX_AUTHOR_LEN)} '),
            Text(f" {('v' + version_str).rjust(VERSION_LEN)} ",
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED))
        ),
    )

@Composable
def CoachbotLine(bot: Coachbot,
                 measurement: MeasurementSpec = MeasurementSpec.INJECTED()):
    """The ``CoachbotLine`` is a UI widget which displays a ``CoachbotState``.

    Parameters:
        bot (Coachbot): The Coachbot whose info should be displayed.
    """
    state = bot.state

    version_str = ('v' + v).rjust(6) \
        if (v := bot.state.os_version) is not None \
        else 'v?.?.?'.rjust(6)

    position_str = f'{round(p.x, 2): 5} {round(p.y, 2): 5}' \
        if (p := state.position) is not None \
        else f"{'?'.rjust(5)},{'?'.rjust(5)}"
    theta_str = f'{round(t * 180 / math.pi, 1): 6}' \
        if (t := state.theta) is not None else f"{'?'.rjust(6)}"

    bat_label = f'{round(v, 2):>4}' if (v := state.bat_voltage) is not None \
        else f'   ?'
    bat_color = (ColorPairs.OK_INVERTED if v > 3.8 \
        else (ColorPairs.WARNING_INVERTED if v > 3.6 \
              else ColorPairs.ERROR_INVERTED)) \
        if (v := state.bat_voltage) is not None else ColorPairs.INFO

    left_widget = Row(
        (
            Text(f' {bot.identifier: 3}▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text(
                ' ✔️  ON   ' if state.is_on else ' ✖️  OFF  ',
                style=TextStyleSpec(
                    color=(ColorPairs.OK_INVERTED if state.is_on else
                           ColorPairs.ERROR_INVERTED),
                    bold=True
                )
            ),
            Text(f' {version_str} '),
            Text(f' [{position_str}] {theta_str}°▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text(f' {bat_label}V ',
                 style=TextStyleSpec(color=bat_color, bold=True)),
        )
    )

    right_widget = Row(
        (
            UserInfo(bot.state.user_code_state),
        )
    )

    return Row(
        (
            left_widget,
            right_widget
        ),
        measurement=measurement,
        layout=LayoutSpec.FILL,
        spacing=RowSpacing.SPACE_BETWEEN
    )
