#!/usr/bin/env python

"""This defines BLE-related errors and exceptions."""


class BLENotReachableError(Exception):
    """Represents an error raised when a Coachbot could not be reached.

    The ``offender`` property indicates which robot failed to be reached.
    """
    def __init__(self, robot, *args: object) -> None:
        self.offender = robot
        super().__init__(*args)
