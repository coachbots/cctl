#!/usr/bin/env python

"""This module defines all the Coachbot-related models."""

import json
from dataclasses import dataclass, asdict
from cctl.utils.math import Vec2


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


@dataclass
class CoachbotState:
    """The StatusMessage is the model that represents the communication between
    coach-os and cctl."""
    is_on: bool
    user_version: str
    os_version: str
    bat_voltage: float
    position: Vec2
    theta: float

    def serialize(self) -> str:
        """Converts the StatusMessage into a serialized form.

        I have decided that this form should be JSON since it is more easily
        debuggable.
        """
        return json.dumps({**asdict(self),
                           'position': [self.position.x, self.position.y]})

    @staticmethod
    def deserialize(data: str) -> 'CoachbotState':
        """Deserializes a StatusMessage from a string."""
        as_dict = json.loads(data)
        return CoachbotState(
            as_dict['is_on'],
            as_dict['user_version'],
            as_dict['os_version'],
            as_dict['bat_voltage'],
            Vec2(as_dict['position']),
            as_dict['theta'])
