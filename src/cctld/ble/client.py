#!/usr/bin/env python

"""This module defines the basic BLE client that is used to communicate with
the Coachbots."""

import asyncio
import logging
from bleak import BleakClient
from cctl.protocols import ble


_UUIDS = {
    'uart': '6E400001-B5A3-F393-E0A9-E50E24DCCA9E',
    'uart-tx-char': '6E400002-B5A3-F393-E0A9-E50E24DCCA9E',
    'uart-rx-char': '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
}


class CoachbotBLEClient(BleakClient):
    """This class defines the basic Client that is used to communicate with the
    Coachbots' Bluefruit boards.
    """
    SLEEP_TIME = 25e-3

    async def __aenter__(self, *args, **kwargs) -> 'CoachbotBLEClient':
        res = await super().__aenter__(*args, **kwargs)
        if kwargs.get('pair'):
            await self.pair()
        return res

    async def toggle_mode(self) -> ble.BluefruitMode:
        """Switches the mode from UART to Command and vice-versa.

        See `The Adafruit Documentation
        <https://learn.adafruit.com/introducing-adafruit-ble-bluetooth-low-energy-friend/standard-at>`_.

        Returns:
            ble.BluefruitMode: The current mode.
        """
        data = await self.request('+++\n'.encode('utf-8'))
        return ble.BluefruitMode.from_bytes(data)

    async def set_mode(self, mode: ble.BluefruitMode) -> None:
        """Sets the mode to the specified mode.

        See `The Adafruit Documentation
        <https://learn.adafruit.com/introducing-adafruit-ble-bluetooth-low-energy-friend/standard-at>`_.

        Parameters:
            mode (ble.BluefruitMode): The target mode to switch to.
        """
        while True:
            try:
                if await self.toggle_mode() == mode:
                    return
            except ble.BluefruitProtocolError:
                pass

    async def set_mode_led(self, value: bool) -> None:
        """Manually sets the mode LED to be on or off.

        See `The Adafruit Documentation
        <https://learn.adafruit.com/introducing-adafruit-ble-bluetooth-low-energy-friend/standard-at>`_.

        Parameters:
            value (bool): Whether the LED should be on or off.

        """
        strv = '1' if value else '0'
        while True:
            try:
                resp = await self.request(
                    f'AT+HWMODELED=5,{strv}\n'.encode('utf-8'))

                if resp.decode('utf-8').split('\r\n')[0] != 'OK':
                    # TODO: Handle failing case
                    pass

                logging.getLogger('bluetooth').debug(
                    'Got response when setting LED: %s', resp)
                return
            except EOFError:
                logging.getLogger('bluetooth').warning(
                    'Received EOF when sending AT+ command.')

    async def read(self) -> bytes:
        """Reads from the Adafruit board.

        Returns:
            bytes: The value that was read.
        """
        value = bytes(await self.read_gatt_char(_UUIDS['uart-rx-char']))
        await asyncio.sleep(self.__class__.SLEEP_TIME)
        return value

    async def write(self, message: bytes) -> None:
        """Write to the Adafruit BLE board.

        Parameters:
            message (bytes): The data to send to the board.
        """
        await self.write_gatt_char(
            _UUIDS['uart-tx-char'],
            message,
            response=True
        )
        await asyncio.sleep(self.__class__.SLEEP_TIME)

    async def request(self, message: bytes) -> bytes:
        """Makes a request to the Coachbot."""
        await self.write(message)
        return await self.read()
