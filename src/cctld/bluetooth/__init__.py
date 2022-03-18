from bluepy import btle

from cctl.api.bot_ctl import Coachbot

MAX_BT_ATTEMPTS = 4


def boot(bot: Coachbot, state: bool) -> bool:
    """Sends a boot signal to the Coachbot BT module.

    Parameters:
        mac_address (str): The MAC address of the Coachbot.
        state (bool): Whether to boot the coachbot on or off.

    Returns:
        bool: Whether the coachbot has received the signal successfully.
    """
    for _ in range(MAX_BT_ATTEMPTS):
        peripheral = btle.Peripheral(bot.mac_address, btle.ADDR_TYPE_RANDOM)
        try:
            serv = list(peripheral.getServices())[-2]  # TODO: Why service -2?
            on_off_char = serv.getCharacteristics()[1]
            for __ in range(2):
                on_off_char.write(f'AT+HWMODELED=5,{1 if state else 0}')
                on_off_char.write('+++\n')

            if bot.is_alive():
                return True
        finally:
            peripheral.disconnect()

    return False
