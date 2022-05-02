#!/usr/bin/env python

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from cctl.utils.math import Vec2


@dataclass
class Coachbot:
    """This class contains all the information about a Coachbot, including its
    identifier and the state."""
    identifier: int
    state: 'CoachbotState'

    @property
    def ip_address(self) -> str:
        """Returns the ip address of this coachbot.

        Todo:
            This implementation may not necessarilly be robust if the network
            changes.
        """
        # TODO: Not robust
        return f'192.168.1.{self.identifier + 3}'


@dataclass
class CoachbotState:
    """The StatusMessage is the model that represents the communication between
    coach-os and cctl."""
    is_on: Optional[bool] = None
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
        print(self)
        return {
            **asdict(self),
            'position': [self.position.x, self.position.y]
            if self.position is not None else None
        }

    @staticmethod
    def from_dict(as_dict: Dict[str, Any]) -> 'CoachbotState':
        """Creates an object from a dictionary.

        Returns:
            CoachbotState: The CoachbotState built from a dictionary.
        """
        return CoachbotState(
            **{**as_dict, 'position': Vec2(as_dict['position'])}
        )

    @staticmethod
    def deserialize(data: str) -> 'CoachbotState':
        """Deserializes a StatusMessage from a JSON string.

        Parameters:
            data (str): The object to be deserialized from JSON.

        Returns:
            CoachbotState: The deserialized object.
        """
        return CoachbotState.from_dict(json.loads(data))
