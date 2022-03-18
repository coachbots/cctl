from typing import Callable, Optional
from cctl import bluetooth
from threading import Thread

from cctl.api.bot_ctl import Coachbot


def set_bot_on(bot: Coachbot,
               state: bool,
               on_success: Optional[Callable] = None,
               on_error: Optional[Callable] = None) -> None:
    """Turns a bot on or off.

    Note:
        This function blocks if and only if either on_success or on_error are
        None. In other words, if you wish to have a non-blocking call, make
        sure you pass an on_success and an on_error. If you don't this function
        will block.

    Parameters:
        identifier (int): The id of the bot.
        state (bool): Whether to turn the bot on or off.
        on_success (Callable): The callback called when the bot state is
            changed.
        on_error (Callable): The callback called if the request fails for some
            reason.
    """
    def _thread_f(on_success: Callable[[], None] = lambda: None,
                  on_error: Callable[[], None] = lambda: None) -> None:
        if bluetooth.boot(bot.mac_address, state):
            on_success()
            return
        on_error()

    on_success_f = lambda: None if on_success is None else on_success
    on_error_f = lambda: None if on_error is None else on_error

    thread = Thread(target=_thread_f, args=(on_success_f, on_error_f))
    thread.start()

    if on_success is None and on_error is None:
        thread.join()
