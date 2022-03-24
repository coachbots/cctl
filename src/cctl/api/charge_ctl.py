"""This module provides functions for controlling the coachbot charging rails"""

from serial import Serial



class ChargeRail:
    """Class representing the charging rail. Use this class for charging rail
    operations.
    """

    def __init__(self, port):
        """Constructs a ChargeRail.
        Parameters:
            port: the serial port to which the charge controller is connected
        """

        self.serial = Serial(port,115200)

    def charge_rail_set(self, power):
        """Changes the state of the charging rail

        Parameters:
            power: if true, the charger will turn on; if false, the charger will turn off
        """
        if power:
            self.serial.write(b'A')
        else:
            self.serial.write(b'D')
        



