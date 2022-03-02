"""This module exposes error codes that may occur during communication with
coach-os."""

from enum import IntEnum


MAX_SUCCESSFUL_VALUE = 32


class NetStatus(IntEnum):
    """Describes a NetStatus.

    All successful network statues must have values less than
        MAX_SUCCESSFUL_VALUE.

    Note:
        NetStatus values need to be in order of severity because only the last
        error result after multiple handlers is kept.
    """
    SUCCESS = 0

    TIMEOUT = 100
    INVALID_RESPONSE = 110
