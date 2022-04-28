#!/usr/bin/env python

import json
from typing import Dict, Any, Tuple
from dataclasses import dataclass, asdict

@dataclass
class CoachbotState:
    """The StatusMessage is the model that represents the communication between
    coach-os and cctl."""
    is_on: bool
    user_version: str
    os_version: str
    bat_voltage: float
    position: Tuple[float, float]
    theta: float

    def serialize(self) -> str:
        """Converts the StatusMessage into a serialized form.

        I have decided that this form should be JSON since it is more easily
        debuggable.
        """
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'position': [self.position.x, self.position.y]
        }

    @staticmethod
    def deserialize(data: str) -> 'CoachbotState':
        """Deserializes a StatusMessage from a string."""
        as_dict = json.loads(data)
        return CoachbotState(
            as_dict['is_on'],
            as_dict['user_version'],
            as_dict['os_version'],
            as_dict['bat_voltage'],
            as_dict['position'],
            as_dict['theta'])

