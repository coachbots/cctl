#!/usr/bin/env python

from compot import ColorPairs, LayoutSpec, MeasurementSpec
from compot.composable import Composable
from compot.widgets import Row, RowSpacing, Text, TextStyleSpec


@Composable
def HeaderLine(measurement: MeasurementSpec = MeasurementSpec.INJECTED()):
    """The ``CoachbotLine`` is a UI widget which displays a ``CoachbotState``.

    Parameters:
        bot (Coachbot): The Coachbot whose info should be displayed.
    """
    left_widget = Row(
        (
            Text('  ID▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text(' Booted▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text('  OS Ver. ▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text(' [  Position ]   Angle▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text(' Batt.▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
        )
    )

    right_widget = Row(
        (
            Text(' User State▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text('           Name          ▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text('      Author     ▕',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True)),
            Text(' User Vers. ',
                 style=TextStyleSpec(color=ColorPairs.INFO_INVERTED,
                                     bold=True))
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
