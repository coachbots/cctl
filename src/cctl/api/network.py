# -*- coding: utf-8 -*-

"""This API module exposes networking utilities that can be used as
necessary.

The only exposed class is Network and it can be used like so:

.. code-block:: python

   net = Network()
   net.user.signal('custom_signal', b'my_byte_data')
   net.user.add_slot('other_signal', lambda signal, data: print(data))

If custom_signal is registered on the coachbots, it will force each coachbot
registered for 'custom_signal' to run the event handler. If other_signal is
ever fired by any coachbot, then the data will be printed.
"""


from cctl.network.user_code_com import UserNetworkEventHandler


class Network:
    """Wraps around all networks."""
    def __init__(self) -> None:
        self._user = None

    @property
    def user(self) -> UserNetworkEventHandler:
        """Returns the UserNetworkEventHandler for communicating with user
        code."""
        if self._user is None:
            self._user = UserNetworkEventHandler()
        return self._user

    def tear_down(self) -> None:
        """Stops all operating network event handlers. You don't usually need
        to call this because it is hooked into __del__
        """
        if self._user is not None:
            self._user.tear_down()

    def __del__(self) -> None:
        self.tear_down()
