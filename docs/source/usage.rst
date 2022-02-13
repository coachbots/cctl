Usage
=====

**cctl** is an incredibly simple utility that you can use to fully control the
Coachbot swarm. In brief, this utility enables you to control all available
aspects of the robots. Aside from being a command-line utility, **cctl** is an
importable package in ``>Python3.6`` exposing various all aspects of robots.
For more information on this, please see `the API documentation <api.html>`_.

The command line utility for **cctl** is also named **cctl**. It follows a
UNIX-like principle for usage. Similarly to ``git``, **cctl** supports various
subcommands to control the swarm. These commands are:

.. code-block:: text

   usage: cctl [-h] {on,off,blink,cam,start,pause,upload,manage} ...

   cctl is the utility for coachbot control.
   
   optional arguments:
     -h, --help            show this help message and exit
   
   command:
     {on,off,blink,cam,start,pause,upload,manage}
                           Control Robot State
       on                  Boot a range of robots up.
       off                 Boot a range of robots down.
       blink               Blinks the LED on specified robots.
       cam                 Coachswarm overhead camera control.
       start               Starts user code on all on robots.
       pause               Pauses user code on all on robots.
       upload              Updates the code on all on robots.
       manage              Starts the management console. This was called
                           init.py in legacy code.

Powering
--------

It is possible to control boot state with the ``on`` and ``off`` commands.

.. code-block:: text

   usage: cctl {on,off} [-h] N [N ...]
   
   positional arguments:
     N           The robot id or range of ids to modify. Format must match one
                 of: [\d], [\d-\d] or "all".
   
   optional arguments:
     -h, --help  show this help message and exit

Both of these commands support multiple arguments meaning you could specify
multiple robots to control as:

.. code-block:: bash

   cctl on 4 8 9

which will turn on robots ``4``, ``8`` and ``9``.

Furthermore, the commands also support a range of robots in the format of
``x-y`` so you can control ranges of robots easily:

.. code-block:: text

   cctl off 4-6 1

which will turn off robots ``4``, ``5``, ``6`` and ``1``.

Finally, you can also specify the keyword ``all`` to control the state of all
robots.

.. code-block:: bash

   cctl off all

which turns off all robots.

User Code
---------

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

.. warning:: This command will ovewrite the current ``usr_code.py`` in your
   `server path` (traditionally ``/home/user/server/server_beta/temp``).

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

.. code-block:: text
   
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
