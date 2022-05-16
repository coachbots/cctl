#!/usr/bin/env python

"""This module defines all the Coachbot-related models."""

from enum import IntEnum
import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, Literal, Union
from cctl.models import CoachbotState, Signal


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

@dataclass
class Request:
    """Represents a Request from the ``Coachbot`` to ``cctld```. This request
    holds the ``CoachbotState`` data."""
    identifier: int
    type: Literal['state', 'signal']
    body: Union[CoachbotState, Signal]

    def serialize(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'identifier': self.identifier,
            'type': self.type,
            'body': self.body.to_dict()
        }

    @staticmethod
    def from_dict(as_dict) -> 'Request':
        return Request(
            identifier=as_dict['identifier'],
            type=(t := as_dict['type']),
            body=(CoachbotState.from_dict(as_dict['body'])
                  if t == 'state'
                  else Signal.from_dict(as_dict['body']))
        )

    @staticmethod
    def deserialize(data: str) -> 'Request':
        return Request.from_dict(json.loads(data))

class StatusCode(IntEnum):
    """Represents a status code."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404


@dataclass
class Response:
    """Represents a simple response to ``coach-os`` from a request. This is
    always a success code."""
    status_code: int = StatusCode.OK

    def serialize(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def deserialize(data: str) -> 'Response':
        return Response(**json.loads(data))
