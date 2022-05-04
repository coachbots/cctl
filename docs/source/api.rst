API
===

The API architecture is twofold. In order to facilitate simple data streams as
well as request-based commands, **cctld** can be interacted with on two fronts
-- through a request-response HTTP-like system and a ``PUBLISH`` model
where any API consumer can ``SUBSCRIBE`` to receive state data as soon as
**cctld** provides it.

Bindings
--------

The API for **cctl** comes in two levels -- a high-level python package called
`cctl.api <cctl.api.html>`__ and a low-level request-response based
language-agnostic API.

The recommended usage is through the high-level package, but, if for whatever
reason you do decide you need to make a custom binding for the API in your own
language, it is documented in the `Low-Level API <api_low_level.html>`__
section.

Quickstart
----------

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

Deep Dive
---------

If you would like to take a deeper dive into the operation of the **cctl** API
interface, please take a look at the following documentation.

I would recommend starting out with the `high-level API
<api_high_level.html>`__ as that is what is primarily intended to be used.

For exact information on the protocols and standards used, please take a look
at the `API Protocol <api_protocol.html>`__ section.

The `Low-Level API <api_low_level.html>`__ section will attempt to introduce
you to a method through which you can interact with **cctld** in any language
you like.

.. toctree::

   api_high_level
   api_protocol
   api_low_level


API Modules
-----------

.. toctree::
   :maxdepth: 6

   api_modules
