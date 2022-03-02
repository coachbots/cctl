Networking in Coach-OS
======================

This section outlines networking as it is implemented currently on coach-os.

coach-os exposes networking-related functions through a event-handler based
system. Similarly to how signals and slots work in the QT framework (if the
reader is familiar with that), coach-os exposes transports for communicating
to cctl and backwards via signals and responds to those events via slots. In
order to successfully communicate, you must abide by these rules. coach-os will
handle the rest.

All networking-related calls are made via ``CCTLNetworkEventHandler``.

Signalling is done via the ``signal`` call. An example of a successful call is:

.. code-block:: python

   my_handler.signal('signal_name', 'my_message'.encode())

This can be called on either ``cctl``'s side of ``coach-os``'s side. If you
have registered a slot for the signal named ``signal_name``, then it will be
fired and will receive the message. For example, to register a slot for
``signal_name``, you can do:

.. code-block:: python

   def _my_handler(signal_name, message):
       print('Received signal %s with message %s' % (signal_name,
                                                     message.decode()))
   my_handler.add_slot('signal_name', _my_handler)

Now, with this slot registered, your signal will be handled by ``_my_handler``.
You can also register multiple slots and they will be handled in order of
registration.

Signals
-------

Types of Signals
^^^^^^^^^^^^^^^^

There are two types of signals that are distinguished in this system:

* Batch signals
* Direct signals

Batch Signals
""""""""""""""

Batch signals are sent from **cctl** to **coach-os** and are sent to all
coachbots. These are published over the wire (using the broadcast ip) and will
be handled by all available coachbots, however, there is no means of knowing
whether a coachbot has actually handled the signal (since the coachbot may, for
example, be turned off or buggy application code may have caused it to
misbehave). These signals are `fire and forget`.

Batch signals cannot be sent from **coach-os** to **cctl**.

You can send these signals via
``cctl_net_handler.signal('my_signal', b'my_data')`` on the side of **cctl**.

Direct Signals
""""""""""""""

Direct signals are signals that are directly sent to a coachbot. These are
possibly slower, however, they yield a guarantee that a signal will, indeed, be
handled (or not). These come in two forms ``cctl -> coach-os`` and ``coach-os
-> cctl``.

The ``cctl -> coach-os`` direct signals can be invoked with:

.. code-block:: python

   coachbot = Coachbot(24)
   def on_success(error_code: int) -> None:
       print('Successful handle of my_signal.')
   def on_error(error_code: int) -> None:
       print('Unsuccessful handle of my_signal.')
   cctl_net_handler.signal(coachbot, 'my_signal', b'my_data',
                           on_success, on_error, timeout=1)

With this, coachbot will attempt to send ``my_signal`` and if it succeeds then
it will fire ``on_success`` with the exit code (for most cases ``0``), while it
will call ``on_error`` if, for some reason, the coachbot errors out or does not
reply within the given timeout interval (in seconds).

The ``coach-os -> cctl`` direct signals are equally as straightforward to use:

.. code-block:: python

   coach_os_net_handler.signal('my_signal', b'my_data',
                               on_success, on_error, timeout=1)

Slots
-----

Slots are the handlers for the `signal` events. These can be registered in two
ways, for **cctl** and **coach-os**.

**cctl**-side
^^^^^^^^^^^^^

The **cctl** slots will provide you with a
``Coachbot`` object that you can use to know which bot is attempting to
communicate with you. For example:

.. code-block:: python

   def handler(signal: str, bot: Coachbot, message: bytes):
       print(f'Received signal {signal} from {bot}: {message}')

   cctl_network.user.add_slot('mysignal', handler)


**coach-os**-side
^^^^^^^^^^^^^^^^^

On the **coach-os** side, the source identity is meaningles (always a central
computer), so the handler can be registered simply as:

.. code-block:: python

   def handler(signal: str, message: bytes):
       print(f'Received signal {signal} from cctl: {message}')

   coach_os_network.user.add_slot('mysignal', handler)

Built-in Signals
----------------

There are currently some built-in signals that are fired from **coach-os**.
These are:

* ``USER_CODE_BEGIN`` - fired when user code starts
* ``USER_CODE_END`` - fired when user code ends

Full Examples
-------------

Here are some more examples that should be more helpful than the previous
snippets usable for reference.

Suppose you are trying to get a coachbot to move on the edges of the field. You
could then write something like:

.. code-block::
   :linenos:
   :caption: Example ``user_code.py``

   import json

   def usr(robot):
       led_color = [255, 255, 255]

       def bully_handler(signal, message):
           nonlocal led_color
           led_color = list(message)

       robot.net.cctl.add_slot('bully', bully_handler)

       while True:
           robot.move_to_corner(0, 0)  # Let's pretend this function exists
           pos = robot.get_pose_blocking()
           robot.net.cctl.signal('corner', json.dumps({
               'x': pos[0],
               'y': pos[1],
               'theta': pos[2]
           }).encode('utf-8'))
           robot.set_led(*led_color)
           robot.delay()

And on **cctl**'s side:

.. code-block:: 
   :linenos:
   :caption: Example ``cctl``-side code.

   from cctl.api.network import Network
   from cctl.api.bot_ctl import Coachbot
   import time

   m_network = Network()

   def corner_handler(signal: str, bot: Coachbot, message: bytes):
       x, y, theta = json.loads(message.decode('utf-8'))
       print(f'{bot} says they\'re on the corner with values {x}, {y}, ' +
             f'{theta}')

       if bot.identifier == 42:
           print('Bullying bot 42 and only 42.')
           color = [x * 10, y * 10, theta * 10]
           m_network.direct_signal('bully', Coachbot(42), bytes(color))

   m_network.add_slot('corner', corner_handler)

   while True:
       time.sleep(1)  # Necessary because Network() spawns its own threads.

Under the Hood
--------------

Under the hood of all of this, ``cctl`` and ``coach-os`` create three ``zmq``
transports -- ``REP``, ``REQ`` and ``PUB/SUB`` (``PUB`` on **cctl**'s side,
``SUB`` on **coach-os**'s). The forecoming table outlines their purposes.

.. list-table:: Outline of Implemented Transports
   :widths: 25 25 25 50 50
   :header-rows: 1

   * - Side
     - Transport
     - Port
     - Purpose
     - Invokation
   * - coach-os
     - REQ
     - 16891
     - Send Signal to CCTL
     - ``coach_os_handler.signal('sig_name', b'message')``
   * - coach-os
     - SUB
     - 16892
     - Receive Batch Signal from CCTL
     - ``coach_os_handler.add_slot('sig_name', handler)``
   * - coach-os
     - REP
     - 16893
     - Receive Individual Signal from CCTL
     - ``coach_os_handler.add_slot('sig_name', handler)``
   * - cctl
     - REQ
     - 16893
     - Send Direct Signal to coach-os
     - ``cctl_handler.signal(coachbot, 'sig_name', b'message', on_success,
       on_error)``
   * - cctl
     - PUB
     - 16892
     - Send batch signal
     - ``cctl_handler.signal('sig_name', b'message')``
   * - cctl
     - REP
     - 16891
     - Receive Individual Signal from CCTL
     - ``cctl.add_slot('sig_name', handler)``

The protocol is relatively standardized. A ``coach-os -> cctl`` signal is
encoded in a message of the following shape:

.. code-block:: haskell

   signal_protocol :: [Char, Integer]
   signal_protocol signal identifier = b64encode(header ++ message)
       where header = padded(encode(signal, "ascii")) ++ padded(identifier)

