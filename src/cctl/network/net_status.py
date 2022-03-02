"""This module exposes error codes that may occur during communication with
coach-os."""

from enum import IntEnum


class NetStatus(IntEnum):
    """Describes a NetStatus."""
    SUCCESS = 0

    INVALID_RESPONSE = 10
    TIMEOUT = 11
