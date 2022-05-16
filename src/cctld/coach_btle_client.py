#!/usr/bin/env python3

"""This module defines the CoachbotBTLEClient class which is to be used to make
requests to the bluetooth modules on the Coachbots.

Todo:
    The way this module is implement is sub-satisfactory. Much of the bugs have
    been shoved under a rug in try-catches. Check the TODO's for more info.
"""

import logging
import asyncio
from enum import IntEnum
from typing import Callable, Coroutine, Iterable, Any
from bluepy import btle

__author__ = 'Marko Vejnovic <contact@markovejnovic.com>'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '1.0.0'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

"""This field defines constants that are used throughout the client. These
constants are to be found on the manufacturer's website and are the UUIDs of
the relevant services.

For the Adafruit Bluefruit, this information is available `here
<https://learn.adafruit.com/
introducing-adafruit-ble-bluetooth-low-energy-friend/uart-service>`__.
"""
BOARD_UUIDS = {
    'adafruit-bluefruit': {
        'uart-service': '6E400001-B5A3-F393-E0A9-E50E24DCCA9E',
        'uart-tx-characteristic': '6E400002-B5A3-F393-E0A9-E50E24DCCA9E',
        'uart-rx-characteristic': '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
    }
}


class CoachbotBTLEMode(IntEnum):
    """The Adafruit Board Supports two modes: UART and COMMAND mode. This enum
    encompasses that information."""
    UART = 0
    COMMAND = 1


class CoachbotBTLEError(Exception):
    """Represents an error that occurred in communicating to the Coachbots."""


class CoachbotBTLEStateException(Exception):
    """Represents an exception raised when a Coachbot bluetooth module cannot
    do the requested operation due to being in a state in which it shouldn't
    be."""


class CoachbotBTLEClient:
    """This class creates a client that you can use to control the bluetooth
    module on the coachbot.

    Example:

    .. code-block:: python

       async with CoachbotBTLEClient('de:ad:ca:fe:fo:od') as client:
           client.set_mode_led_on(True)

    """
    def __init__(self, address: str, iface=0, max_attempts=5) -> None:
        """Initializes a CoachbotBTLEClient.

        Parameters:
            address (str): The MAC address of the target coachbot btle module.
            iface (int): The interface to be used. Check for this in
                ``hciconfig`` For ``hci0`` this value will be ``0``.

        Note:
            This function raises a ``bluepy.btle.BTLEException`` if it cannot
            connect to the device.
        """
        self._address = address
        self._iface = iface
        self.peripheral = None
        self.uart_service = None
        self.tx_channel = None
        self.rx_channel = None
        self.max_attempts = max_attempts

    async def set_mode(self, mode: CoachbotBTLEMode) -> None:
        """Sets the mode of the coachbot to the target mode.

        The implementation here is somewhat reduntant since there is no AT+
        command to check for the current mode. We have to switch until we get
        to the right mode.

        Raises:
            CoachbotBTLEError: Raised when the coachbot could not change the
            mode.
        """
        async def __helper():
            while await self.toggle_mode() != mode:
                pass

        attempt = 0
        while attempt < self.max_attempts:
            try:
                await __helper()
                attempt += 1
                return
            except CoachbotBTLEError as err:
                logging.getLogger('bluetooth').warning(
                    'Could not toggle the mode to %s due to %s. Trying again.',
                    mode, err)
        raise CoachbotBTLEError('Could not change the mode of %s to %s.',
                                self._address, mode)

    async def toggle_mode(self) -> CoachbotBTLEMode:
        """Switches the mode of the Coachbot.

        Returns:
            CoachbotBTLEMode: The mode that the Coachbot Adafruit is in after
            the switch.
        """
        message = '+++\n'.encode('ascii')
        logging.getLogger('bluetooth').debug('Sending message %s', message)
        assert self.tx_channel is not None
        self.tx_channel.write(message)
        await asyncio.sleep(1e-1)

        assert self.rx_channel is not None
        reply = self.rx_channel.read().decode('ascii')

        if 'OK' not in reply:
            raise CoachbotBTLEError('Could  not toggle mode.The reply was not'
                                    f'OK. The reply was: {reply}')

        # TODO: This hack here is done because sometimes the rx channel returns
        # a reply of \r (due to message reading not being properly
        # protocolized, and a likely mistiming issue).
        try:
            return CoachbotBTLEMode(int(reply[0]))
        except ValueError as err:
            raise CoachbotBTLEError from err

    async def set_mode_led_on(self, state: bool) -> None:
        """Attempts to turn on/off the MODE LED (Red) on of the specified
        Coachbot BT module.

        Parameters:
            state (bool): Whether the LED should turn on or off.

        Raises:
            CoachbotBTLEStateException: If this function is called but the
                Adafruit board is not in Command mode. Calling ``toggle_mode``
                will alleviate the problem and move the Coachbot Adafruit to
                command mode.
        """
        async def __helper() -> None:
            message = f'AT+HWMODELED=5,{1 if state else 0}\n'.encode('ascii')
            logging.getLogger('bluetooth').debug('Sending message %s', message)
            assert self.tx_channel is not None
            self.tx_channel.write(message)
            await asyncio.sleep(1e-1)

            assert self.rx_channel is not None
            reply = self.rx_channel.read().decode('ascii')

            # A no-reply indicates that we are not in command mode.
            if reply == '':
                raise CoachbotBTLEStateException(
                    'The Adafruit is not in command mode.')

            if 'OK' not in reply:
                raise CoachbotBTLEError('The reply was not OK. The reply was: '
                                        f'{reply}')

        for _ in range(self.max_attempts):
            try:
                await __helper()
                return
            except CoachbotBTLEError as err:
                logging.getLogger('bluetooth').warning(
                    'Could not boot bot due to %s. Will retry.', err)
        logging.getLogger('bluetooth').error(
            'Could not boot bot.')

    async def __aenter__(self) -> 'CoachbotBTLEClient':
        def peripheral_allocate() -> btle.Peripheral:
            return btle.Peripheral(
                self._address, addrType=btle.ADDR_TYPE_RANDOM,
                iface=self._iface)

        for _ in range(self.max_attempts):
            try:
                self.peripheral = await asyncio.get_event_loop() \
                    .run_in_executor(executor=None, func=peripheral_allocate)
                assert self.peripheral is not None
                self.uart_service = self.peripheral.getServiceByUUID(
                    BOARD_UUIDS['adafruit-bluefruit']['uart-service'])

                assert self.uart_service is not None
                self.tx_channel = self.uart_service.getCharacteristics(
                    BOARD_UUIDS['adafruit-bluefruit']['uart-tx-characteristic']
                )[0]
                self.rx_channel = self.uart_service.getCharacteristics(
                    BOARD_UUIDS['adafruit-bluefruit']['uart-rx-characteristic']
                )[0]

                return self
            except btle.BTLEException:
                logging.getLogger('bluetooth').warning(
                    'Could not connect to device %s. Trying again...',
                    self._address)
        logging.getLogger('bluetooth').warning(
            'Failed to connect to device %s. Giving up.', self._address)
        raise CoachbotBTLEError('Connection error to device %s')

    async def __aexit__(self, exc_t, exc_tb, exc_v) -> bool:
        if self.peripheral is not None:
            self.peripheral.disconnect()
        return False


class CoachbotBTLEClientManager:
    """This manager class uses a queue to maximize the work that clients can
    do."""
    def __init__(self, interfaces: Iterable[int]) -> None:
        self._available_interfaces: asyncio.Queue[int] = asyncio.Queue()
        for interface in interfaces:
            self._available_interfaces.put_nowait(interface)

    async def execute_request(
        self,
        addr: str,
        request: Callable[[CoachbotBTLEClient], Coroutine[Any, Any, None]]
    ):
        """This manager allows you to safely manage clients. Because only one
        client can exist per interface, this function will ensure that you will
        wait until there is an available interface for you to use.

        Parameters:
            addr (str): The MAC address of the target to execute the command
                on. Must be a Coachbot Adafruit.
            request: (Coroutine[Any, Any,
                Callable[[CoachbotBTLEClient], None]]): An async callable that
                will get called whenever there is a free interface.

        Example:

        .. code-block:: python

           manager = BTLEClientManager([0, 2])
           async def boot_bot(client):
               try:
                   await client.set_mode_led_on(True):
               except CoachbotBTLEStateException as cbtles_ex:
                   await client.toggle_mode()
                   await client.set_mode_led_on(True)

           asyncio.gather(
               manager.execute_request(boot_bot, Coachbot(90).mac_address)
               manager.execute_request(boot_bot, Coachbot(80).mac_address)
               # This call will have to wait until the other ones are done.
               manager.execute_request(boot_bot, Coachbot(90).mac_address)
           )
        """
        interface = await self._available_interfaces.get()
        try:
            async with CoachbotBTLEClient(addr, interface) as client:
                await request(client)
        finally:
            await self._available_interfaces.put(interface)