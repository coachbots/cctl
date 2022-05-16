#!/usr/bin/env python

import json
import importlib.resources as pkg_resources
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from cctl.utils.math import Vec2
import cctl_static


COACHBOT_MAC_ADDRESSES = pkg_resources.read_text(
    cctl_static, 'coachbot_btle_mac_addresses').split('\n')


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

    @property
    def bluetooth_mac_address(self) -> str:
        """Returns the mac address of this coachbot's bluetooth module."""
        return COACHBOT_MAC_ADDRESSES[self.identifier]


@dataclass
class UserCodeState:
    """Represents the state of user code."""
    is_running: Optional[bool] = None
    version: Optional[str] = None
    name: Optional[str] = None
    author: Optional[str] = None
    requires_version: Optional[str] = None
    user_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts this object to a dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(as_dict) -> 'UserCodeState':
        return UserCodeState(**as_dict)


@dataclass
class CoachbotState:
    """The StatusMessage is the model that represents the communication between
    coach-os and cctl."""
    is_on: Optional[bool] = None
    os_version: Optional[str] = None
    bat_voltage: Optional[float] = None
    position: Optional[Vec2] = None
    theta: Optional[float] = None
    user_code_state: UserCodeState = UserCodeState()

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
            'user_code_state': self.user_code_state.to_dict(),
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
            **{
                **as_dict,
                'user_code_state':
                    UserCodeState.from_dict(as_dict['user_code_state']),
                'position': Vec2(as_dict['position']) \
                    if as_dict['position'] is not None else None
            }
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


@dataclass
class Signal:
    """Represents a signal that is sent from a coachbot to cctld."""
    name: str
    body: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(as_dict: Dict[str, Any]) -> 'Signal':
        return Signal(**as_dict)
