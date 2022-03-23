"""This module provides functions for controlling the coachbot charging rails"""

from Serial import serial

"""Changes the state of the charging rail

Parameters:
    port: the serial port to which the charge controller is connected
    power: if true, the charger will turn on; if false, the charger will turn off
"""
def charge_rail_set(port, power):
    s = serial.(port,115200)
    if power:
        s.write('A')
    else:
        s.write('D')
    s.close()
    

