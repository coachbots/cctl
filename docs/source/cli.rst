Command Line Usage
==================

**cctl** supports CLI usage which is documented here. Documentation is also
available as a manpage so you can run ``man cctl`` to get helpful information
in the terminal. The CLI utility will expose as much data as it can to you.

The utility has been designed to have various subcommands each of which have
their own flags. In-depth information is available in the manpage, however,
more easily digestable information is available here.

Powering
--------

The ``on`` and ``off`` subcommands control Coachbots being on and off. For
example:

.. code-block:: bash

   cctl on 4 8 9

turns on robots ``4``, ``8`` and ``9``. These commands also support ranges so
you can do:

.. code-block:: bash

   cctl off 4-6 1

which will turn off robots ``4``, ``5``, ``6`` and ``1``.

Finally, you can also pass the ``all`` parameter which will turn the whole
swarm on or off.

.. code-block:: bash

   cctl off all

.. warning::

   These commands may take a long while, especially if there is difficulty
   communicating with the Coachbots. Please do not fret, the command will
   eventually finish, just give it time.

   If you do decide to interrupt the command with ``<CTRL>+{D/C}``, note that
   all the bots you requested to boot will still end up booting.


Controlling User Code
---------------------

User code is controlled with the ``start``, ``pause`` and ``upload``
subcommands.

Starting and Stopping
^^^^^^^^^^^^^^^^^^^^^

The subcommands ``start`` and ``pause`` control user code.

You can start and pause user code as:

.. code-block:: bash

   cctl start
   cctl pause

.. note:: Unlike ``on`` and ``off`` these commands do not support robot ids.
   Rather, these commands start and pause user code on all powered robots.

Uploading
^^^^^^^^^

The subcommand ``upload`` uploads a new user code script onto the coachbots.
The format of this command is:

.. code-block:: text

   usage: cctl upload [-h] [--operating-system] PATH
   
   positional arguments:
     PATH                  The path to the user code.
   
   options:
     -h, --help            show this help message and exit
     --operating-system, -o
                           Uploads a fresh copy of the OS as well as the user
                           code.

Contrary to the original implementation of uploading where ``usr_code.py`` had
to be explicitly named as such and located in the server directory
(traditionally ``/home/user/coach/server_beta/temp``), this command consumes a
path to the target user code script which may be named however you like. In
other words, if you have a script:

.. code-block:: python
   :linenos:
   :caption: my_file.py

   def usr(robot):
      while True:
         robot.set_led(100, 0, 0)
         robot.delay()

you can simply invoke:

.. code-block:: bash

   cctl upload my_file.py

If you wish to re-upload the operating system as well, simply pass the ``-o``
flag to upload:

.. code-block:: bash

   cctl upload -o my_file.py

which will reinstall the operating system with the latest one available in your
``server_path/temp`` before uploading ``my_file.py``.


Blinking
--------

The ``blink`` subcommand enables you to turn on the LEDs on the coachbots in
order to identify them. It operates similarly to ``on`` and ``off``:

.. code-block:: bash
   
   cctl blink 1 4 8-9

Camera Control
--------------

The ``cam`` subcommand controls the overhead camera available above the
coachbot playfield. This subcommand further supports the commands ``setup`` and
``preview``.

Setup
^^^^^

The ``setup`` command is used to setup the required video stream [#setup-fn]_.
You can run

.. code-block:: bash

   cctl cam setup

to setup all required video streams. Unless you have run this, you will be
unable to see any sensible video output.

Preview
^^^^^^^

The ``preview`` subcommand simply opens an ``ffplay`` instance for previewing
video output.

.. code-block:: bash

   cctl cam preview

.. rubric:: Footnotes

.. [#setup-fn] Specifically, this command makes a loopback v4l2 device that is
   used as the postprocessing sink and runs the postprocessing from the webcam
   input into the newly created sink. The webcam itself has significant lens
   distortion (due to how wide the FOV is) so we use the ``ffmpeg``
   ``lenscorrection`` filter to compensate for this.
