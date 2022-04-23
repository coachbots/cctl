#!/usr/bin/env python

"""This module exposes various models that cctld uses."""

import json
from dataclasses import asdict, dataclass
from cctl.utils.math import Vec2


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

    def serialize(self) -> bytes:
        """Converts the StatusMessage into a serialized form.

        I have decided that this form should be JSON since it is more easily
        debuggable.
        """
        return json.dumps(asdict(self)).encode('ascii')

    @staticmethod
    def deserialize(data: bytes) -> 'CoachbotState':
        """Deserializes a StatusMessage from bytes."""
        as_dict = json.loads(data.decode('ascii'))
        return CoachbotState(
            as_dict['is_on'],
            as_dict['user_version'],
            as_dict['os_version'],
            as_dict['bat_voltage'],
            as_dict['position'],
            as_dict['theta'])
