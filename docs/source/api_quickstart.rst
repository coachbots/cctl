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
   # Boots up bots 4 and 9 and boots down bot 1
   cctl_bots.boot_bots([4, 1, 9], [True, False, True])
   # Boots up bots 4, 9 and 1
   cctl_bots.boot_bots([4, 1, 9], True)
   # Boots down all bots
   cctl_bots.boot_bots('all', False)

   cctl_bots.boot_bot(1, True)  # Boots up bot 1
   cctl_bots.blink(1)  # Blinks bot 1
   # Uploads the user code without replacing the operating system.
   cctl_bots.upload_code('/home/me/my_usr_code.py', False)
   cctl_bots.set_user_code_running(True)  # Starts user code
   cctl_bots.set_user_code_running(False)  # Pauses user code
