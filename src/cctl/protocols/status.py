#!/usr/bin/env python

"""This module defines all the Coachbot-related models."""

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict
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
class Request:
    """Represents a Request from the ``Coachbot`` to ``cctld```. This request
    holds the ``CoachbotState`` data."""
    identifier: int
    state: 'CoachbotState'

    def serialize(self) -> str:
        return json.dumps({
            'identifier': self.identifier,
            'state': self.state.to_dict()
        })

    @staticmethod
    def deserialize(data: str) -> 'Request':
        as_dict = json.loads(data)
        return Request(
            identifier=as_dict['identifier'],
            state=CoachbotState.deserialize(as_dict['state'])
        )


@dataclass
class Response:
    """Represents a simple response to ``coach-os`` from a request. This is
    always a success code."""
    status_code: int = 0

    def serialize(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def deserialize(data: str) -> 'Response':
        return Response(**json.loads(data))
