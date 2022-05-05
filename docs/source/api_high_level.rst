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
   CCTLD_HOST = 'ipc:///var/run/cctld/request_feed'

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
   CCTLD_HOST = 'ipc:///var/run/cctld/request_feed'

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

Observable
----------

Besides exposing this admitely HTTP-like API, **cctld** also tries to be
helpful in giving you some ``Observable`` objects that you can then
``Observe``. For example:

.. code-block:: python
   :linenos:
   :name: Tracking Coachbot State
   :caption: Tracking Coachbot State

   #!/usr/bin/env python3.8

   import asyncio
   from reactivex import operators as rxops
   from cctl.api.cctld import CCTLDCoachbotStateObservable
   from cctl.models import CoachbotState

   # Note the change here.
   CCTLD_HOST = 'ipc:///var/run/cctld/state_feed'

   async def main():
       # Note that this observable returns a 100-tuple of CoachbotState
       # objects.
       my_obserable, task = CCTLDCoachbotStateObservable(CCTLD_HOST)

       # We print all coachbot states as they come in
       my_obserable.subscribe(on_next=lambda states: print(states))

       # We could also track specific coachbot states like so:
       # Note that we will still pritn 100-tuples, but only those in which the
       # first bot is on.
       my_obserable.pipe(
           rxops.filter(lambda states: states[0].is_on)).subscribe(
               lambda states: print(states))

       # You can always pipe this through if you are only interested in the
       # first bot.
       my_obserable.pipe(
           rxops.filter(lambda states: states[0].is_on)).subscribe(
               lambda states: print(states[0]))

       # Do not forget to await for the task! Otherwise we're just going to
       # pass through without continually listening.
       await task

   if __name__ == '__main__':
       asyncio.run(main())

Now that's all fine and dandy, but if you're interested in signals as they're
fired on the Coachbots you can track that too with the
``CCTDLSignalObservable`` in a very similar fashion. Think of these as rising
edges to the previous being actual values in electrical signals.

.. code-block:: python
   :linenos:
   :name: Tracking Coachbot Signals
   :caption: Tracking Coachbot Signals

   #!/usr/bin/env python3.8

   import asyncio
   from reactivex import operators as rxops
   from cctl.api.cctld import CCTLDSignalObservable
   from cctl.models import Signal

   # Note the change here.
   CCTLD_HOST = 'ipc:///var/run/cctld/signal_feed'

   async def main():
       # This observable will give you cctl.models.Signal objects.
       my_obserable, task = CCTLDSignalObservable(CCTLD_HOST)

       # We track all of the signals.
       my_obserable.subscribe(on_next=lambda signal: print(signal))

       # We can track specific signals too!
       my_obserable.pipe(
           rxops.filter(lambda sig: sig.name == 'user-code-begin').subscribe(
               on_next=lambda sig: print(sig))

       # Do not forget to await for the task! Otherwise we're just going to
       # pass through without continually listening.
       await task

   if __name__ == '__main__':
       asyncio.run(main())

What you choose between these two is completely up to you!
