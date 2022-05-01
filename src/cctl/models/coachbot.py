#!/usr/bin/env python

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from cctl.utils.math import Vec2


@dataclass
class CoachbotState:
    """The StatusMessage is the model that represents the communication between
    coach-os and cctl."""
    is_on: bool = False
    user_version: Optional[str] = None
    os_version: Optional[str] = None
    bat_voltage: Optional[float] = None
    position: Optional[Vec2] = None
    theta: Optional[float] = None
    user_code_running: Optional[bool] = None

    def serialize(self) -> str:
        """Converts the StatusMessage into a serialized form.

        Returns:
            str: The JSON representation of this object.
        """
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Converts this object into a dictionary.

        Returns:
            Dict[str, Any]: This object in dictionary form, ready to be
                serialized.
        """
        return {
            **asdict(self),
            'position': [self.position.x, self.position.y]
            if self.position is not None else None
        }

    @staticmethod
    def deserialize(data: str) -> 'CoachbotState':
        """Deserializes a StatusMessage from a JSON string.

        Parameters:
            data (str): The object to be deserialized from JSON.

        Returns:
            CoachbotState: The deserialized object.
        """
        as_dict = json.loads(data)
        return CoachbotState(
            is_on=as_dict['is_on'],
            user_version=as_dict['user_version'],
            os_version=as_dict['os_version'],
            bat_voltage=as_dict['bat_voltage'],
            position=as_dict['position'],
            theta=as_dict['theta'],
            user_code_running=as_dict['user_code_running']
        )
