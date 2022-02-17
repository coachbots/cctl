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
