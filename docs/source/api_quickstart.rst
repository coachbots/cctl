Quickstart
----------

You can simply get started with **cctl**'s API by importing it and using
functions from it:

.. code-block:: python
   :linenos:

   import cctl.api.configuration as cctl_conf
   print(cctl_conf.get_server_dir())  # Returns the server directory.
   print(cctl_conf.get_server_interface())  # Returns the netinterface

   import cctl.api.bot_ctl as cctl_bots

   # Note the implementation has changed mildly for the following operations.
   # There is a nice class you can now use:
   my_bot = cctl_bots.Coachbot(1)

   # Blinks the bot!
   my_bot.blink()

   # Boots up coachbot 1 and blocks execution until it fully boots.
   my_bot.boot(True)

   # Checks if my_bot is alive (although, that is guaranteed after a boot_bot
   # call)
   my_bot.is_alive()  # Definitely True!

   # This will block forever.
   my_bot.wait_until_state(False)

   # Pretending we didn't make that bad call,
   my_bot.boot(False)

   # Redundant because boot(False) guarantees this.
   my_bot.wait_until_state(False)

   # Also, you can build a Coachbot from an IP address:
   my_other_bot = cctl_bots.Coachbot.from_ip_address('192.168.1.24')

   # Let's get its address
   my_other_bot.address  # -> 192.168.1.24

   # Let's boot two bots:
   cctl_bots.boot_bots([my_bot, my_other_bot], True)

   # Both are guaranteed to be booted and network-reachable.
   cctl_bots.get_alives()  # Returns [Coachbot(1), Coachbot(21)]

   # Uploads the user code without replacing the operating system.
   cctl_bots.upload_code('/home/me/my_usr_code.py', False)
   cctl_bots.set_user_code_running(True)  # Starts user code

   # Let's let that user code play for a while.
   sleep(5)

   cctl_bots.set_user_code_running(False)  # Pauses user code

Networking
^^^^^^^^^^

Networking is a whole can of worms on this project, but **cctl** and
**coach-os** theoretically have a nice API that you can use. Most of the API
right now is broken, but the following is fully functional and usable.

Briefly, communication between the Coachbots and **cctl** is done in an
event-based system. What this means is that you have two main functions that
you can use for handling data. These functions are, in spirit, similar to QTs
``signal``'s and ``slot``'s, hence the two functions are named ``signal`` and
``add_slot``. These functions are basically an event-trigger and an
event-handler registration hooks.

The core idea is that when you fire a ``signal``, every ``slot`` registered for
that ``signal`` will be fired and an appropriate handler will be called. This
works both when firing signals from the Coachbot and when firing from CCTL
(although the latter has a bug).

For example:

.. code-block:: python

   # On CCTL's end:
   from cctl.api.network import Network
   from cctl.network.signals import USER_CODE_BEGIN, USER_CODE_END

   my_network = Network()

   counter = 0
   # Note, the handler does not tell you which robot is messaging you. I will
   # fix this. A dirty hack you can use now is to encode this in data (ie. copy
   # the legacy implementation).
   def _my_signal_handler(signal: str, data: bytes):
       nonlocal counter
       counter += 1
       print(f'Received signal: {signal}, with message: {data}')
       print(f'So far, I\'ve received {counter} messages.')

   def _on_begin(signal: str, _):
      print('User code is starting on a coachbot.')

   def _on_end(signal: str, data: bytes):
      print('User code has ended on a robot (but I don\'t know which one).')

   my_network.user.add_slot(USER_CODE_BEGIN, _on_begin)
   my_network.user.add_slot(USER_CODE_END, _on_end)
   my_network.user.add_slot('my_custom_signal', _handler)

   # If you're not going to do anything here, you need to wait for the Network
   # thread to finish. If you do nothing, your program will just exit.
   my_network.user.worker.join()  # This call will be improved sometime.


   # In the coachbot user code
   # ...
   robot.net.cctl.signal('my_custom_signal', b'my_data')
   # ...

Now, whenever ``my_custom_signal`` is fired, **cctl** will call
``_my_signal_handler`` and your code will execute.

There is a couple of signals you mind find useful that come by default:
``cctl.network.signals.{USER_CODE_BEGIN,USER_CODE_END}``. These are fired when
user code begins and ends (successfully). If an error is found, some catch-all
exception handler somewhere in coach-os catches it and USER_CODE_END may not be
fired. If you return from ``usr``, it should be fired.

You can do the exact converse as well (in theory, but there's a bug):

.. code-block:: python

   # On CCTL's end:
   my_network = Network()
   my_network.user.signal('my_custom_signal', b'my_data')


   # In the coachbot user code
   # ...
   def _handler(signal_type, data):
       robot.logger.info('Received signal %s', signal_type)
   robot.net.cctl.add_slot('my_custom_signal', _handler)
   # ...


.. note:: This transport will signal ``my_custom_signal`` to all robots on the
   network. This means that all robots will receive this.

.. warning:: Sadly, the last code-example won't work. It's currently broken
   somewhere, and I don't know where. I used a PUB-SUB architecture here to
   make all robots respond to the signal, but I have a bug somewhere.

Finally, you can talk directly to Coachbots...

.. warning:: Not implemented.
