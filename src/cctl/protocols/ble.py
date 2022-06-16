#!/usr/bin/env python

from dataclasses import dataclass


class BluefruitProtocolError(Exception):
    """Represents an error raised when communicating with the Bluefruit
    board."""


@dataclass
class BluefruitMode:
    """Represents a BluefruitMode that can be retrieved/pushed onto the
    Bluefruit board."""
    command: bool

    @staticmethod
    def from_bytes(value: bytes) -> 'BluefruitMode':
        """Creates a BluefruitMode from bytes."""
        if len(value) != len(b'0\r\nOK\r\n'):
            raise BluefruitProtocolError('Invalid response length.')

        response = value.decode('utf-8').split('\r\n')

        if len(response) != 3:
            raise BluefruitProtocolError('Invalid Response Size.')

        if response[1] != 'OK':
            raise BluefruitProtocolError('OK Not Returned.')

        if response[0] not in ('0', '1'):
            raise BluefruitProtocolError('Invalid Response Value.')

        return BluefruitMode(response[0] == '1')
