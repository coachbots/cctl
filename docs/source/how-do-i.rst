How Do I ...?
=============

This documentation section is written mostly to have a Q&A format for commonly
asked questions with **cctl** or things you might want to do that may be
useful. In other words, this section is to fully replace the legacy `Coachbot
documentation`.

Get To Work After Entering The Lab
----------------------------------

Ensure you have the control computer turned on, connected to the router and let
**cctld** do the automatic negotiation with the coachbots from there.

Start The Management Interface
------------------------------

.. code-block:: bash

   cctl status --tui

Turn On Robots
--------------

.. code-block:: bash

   cctl on 90 # For one robot
   cctl on 90,95 # For two robots
   cctl on 90-99 # For a range of robots
   cctl on all # For all robots

Upload My Custom User Script
----------------------------

.. code-block:: bash

   cctl upload path/to/my/usr_code.py
   # CCTL does not require you to name your file usr_code.py
   cctl upload -o path/to/test_mass.py # If you want to reinstall coach-os

Start Running My User Code
--------------------------

.. code-block:: bash

   cctl start

Pause My User Code
------------------

.. code-block:: bash
   
   cctl pause

Get Remote Terminal Access Into the Robot
-----------------------------------------

.. code-block:: bash

   BOT_ID=90 ssh pi@192.168.1.$(($BOT_ID + 3))
