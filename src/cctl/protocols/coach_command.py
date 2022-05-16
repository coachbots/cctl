#!/usr/bin/env python

"""This module defines the protocol that is used to send commands to the
Coachbots."""

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Dict, Any


@dataclass
class Request:
    """Represents a basic command request."""
    method: str
    endpoint: str
    head: Dict[str, Any] = field(default_factory=lambda: {})
    body: Dict[str, Any] = field(default_factory=lambda: {})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(as_dict: Dict[str, Any]) -> 'Request':
        return Request(**as_dict)


class StatusCode(IntEnum):
    """Represents a response status code."""
    OK = 200

    STATE_CONFLICT = 409


@dataclass
class Response:
    """Represents a basic command response."""
    status_code: StatusCode

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(as_dict: Dict[str, Any]) -> 'Response':
        return Response(**as_dict)
