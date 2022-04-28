#!/usr/bin/env python

"""This module exposes all the IPC-related models."""

import json
from enum import IntEnum
from dataclasses import asdict, dataclass, field
from typing import Any, Dict


__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.6.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'


VALID_METHODS = ('create', 'read', 'update', 'delete')


@dataclass
class Request:
    """Represents a basic IPCRequest that cctld supports."""
    method: str
    endpoint: str
    head: Dict[str, Any] = field(default_factory=lambda: {})
    body: str = ''

    def serialize(self) -> str:
        """Converts an IPCRequest into an JSON tring."""
        return json.dumps(asdict(self))

    @staticmethod
    def deserialize(data: str) -> 'Request':
        """Creates an IPCRequest from a JSON string."""
        return Request(
            (as_dict := json.loads(data))['method'],
            as_dict['endpoint'],
            as_dict['head'],
            as_dict['body']
        )


class ResultCode(IntEnum):
    """Enumerates all valid IPC result codes. These are a smaller subset of
    HTTP response codes.
    """
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405


@dataclass
class Response:
    """Represents a basic IPCResponse that cctld supports."""
    result_code: ResultCode
    body: str = ''

    def serialize(self) -> str:
        """Converts self into a string representation using JSON."""
        return json.dumps(asdict(self))

    @staticmethod
    def deserialize(data: str) -> 'Response':
        """Creates an IPCResponse from a string."""
        return Response(
            (as_dict := json.loads(data))['result_code'],
            body=as_dict['body']
        )
