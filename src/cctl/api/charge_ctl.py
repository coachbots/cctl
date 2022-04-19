"""
This module provides functions for controlling the coachbot charging rails
"""

__author__ = 'Billie Strong'
__copyright__ = 'Copyright 2022, Northwestern University'
__credits__ = ['Marko Vejnovic', 'Lin Liu', 'Billie Strong']
__license__ = 'Proprietary'
__version__ = '0.5.1'
__maintainer__ = 'Marko Vejnovic'
__email__ = 'contact@markovejnovic.com'
__status__ = 'Development'

from cctl.daughters import arduino


async def charge_rail_set(power: bool) -> None:
    """Changes the state of the charging rail

    Parameters:
        power (bool): Whether to set the power on or off.
    """
    await arduino.charge_rail_set(power)
