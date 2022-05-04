High Level Python API
^^^^^^^^^^^^^^^^^^^^^

In this section I will attempt to document the higher-level python API that can
be used for interfacing with **cctld**.

Request Response
----------------

In order to interface with the request-response system of **cctld** you can use
the `CCTLDClient <api_modules.html#cctl.api.cctld.CCTLDClient>`_ class. This is
a class that is designed to be used as a context manager (and will throw
exceptions if you do not use it as one). All uses of this class will guarantee
atomic operations.

.. note::

   This class will create a new `zmq.Context
   <http://api.zeromq.org/2-1:zmq-init>`_ every time you use it. You should use
   one client throughout your whole application.


A couple of examples to get you started are:

.. code-block:: python
   :linenos:
   :name: Reading Coachbot State
   :caption: Reading Coachbot State

   #!/usr/bin/env python3.8

   import asyncio
   from cctl.api.bot_ctl import Coachbot
   from cctl.api.cctld import CCTLDClient

   # This should match the value in /etc/coachswarm/cctld.conf
   CCTLD_HOST = 'ipc:///var/run/cctld/request_pipe'

   async def main():
       with CCTLDClient(CCTLD_HOST) as client:
           # Let us read the state of the coachbot.
           state = await client.read_bot_state(Coachbot(90))
           print(f'The bot state is currently {state}')

           # A None bat_voltage indicates that cctld does not know the bat
           # voltage (probably because the bot is off).
           # This goes for all other properties of state.
           print(f'The bat_voltage is {v}'
                 if (v := state.bat_voltage) is not None
                 else 'cctld doesn\'t know the battery voltage of the bot.')

    if __name__ == '__main__':
        asyncio.run(main())

So you don't have to write loops in getting the coachbot state, you can simply
do:

.. code-block:: python
   :linenos:
   :name: Reading All Coachbot States
   :caption: Reading All Coachbot States

   #!/usr/bin/env python3.8

   import asyncio
   from cctl.api.bot_ctl import Coachbot
   from cctl.api.cctld import CCTLDClient

   # This should match the value in /etc/coachswarm/cctld.conf
   CCTLD_HOST = 'ipc:///var/run/cctld/request_pipe'

   async def main():
       with CCTLDClient(CCTLD_HOST) as client:
           # Let us read the state of the coachbot.
           states = await client.read_bots_state()
           on = tuple(Coachbot(i) if b.is_on for i, b in enumerate(states))
           off = tuple(Coachbot(i) if not b.is_on for i, b in enumerate(states))
           print(f'Coachbots {on} are on and {off} are off.')

    if __name__ == '__main__':
        asyncio.run(main())


Note that the ``CCTLDClient`` client methods are all ``async`` methods. This is
done so that you can wait for the result of an operation. You are not obliged
to ``await`` these coros and can simply run them as a task waiting for their
result.

.. code-block:: python
   :linenos:
   :name: Starting/Stopping User Code
   :caption: Starting/Stopping User Code

   #!/usr/bin/env python3.8

   import asyncio
   from cctl.api.bot_ctl import Coachbot
   from cctl.api.cctld import CCTLDClient

   # This should match the value in /etc/coachswarm/cctld.conf
   CCTLD_HOST = 'ipc:///var/run/cctld/request_pipe'

   async def doesnt_care_about_user_code_running():
       await asyncio.sleep(5)

   async def cares_about_user_code_running():
       await asyncio.sleep(5)

   async def main():
       with CCTLDClient(CCTLD_HOST) as client:
           try:
               task = asyncio.create_task(
                   client.set_user_code_running(Coachbot(90), True))

               # Call a function that doesn't really care about user code.
               await doesnt_care_about_user_code()

               # By this point, the task has likely finished. Let's await it to
               # make sure.
               await task

               await cares_about_user_code_running()

           except CCTLDRespInvalidState as err:
               print('The coachbot state could not be changed. '
                     'Check if it is off.')

   if __name__ == '__main__':
       asyncio.run(main())
