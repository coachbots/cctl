Configuration
-------------

**cctl** requires some minor manual configuration to be done before you can
fully use it.

Setting up a Proxy User
^^^^^^^^^^^^^^^^^^^^^^^

**cctld** requires a specific user it can use to setup secure proxying between
**coach-os** and itself. You can create this user by running:

.. code-block:: bash

   useradd coachbot_proxy

Take note of the password you create.
It is also necessary to register the public keys of the coachbots with the
``coachbot_proxy`` user, so, you can do that with:

.. code-block:: bash

   export MY_PASS=<YOUR-PASSWORD>
   for bot in {93..103}; do
       ssh pi@192.168.1.$bot \
           "ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_coachbot_proxy"
       ssh pi@192.168.1.$bot "cat ~/.ssh/id_coachbot_proxy.pub" | \
           cat > /tmp/id_coachbot_proxy.pub
       echo $MY_PASS | sudo -S -u coachbot_proxy sh -c \
           "mkdir -p /home/coachbot_proxy/.ssh; \
           cat /tmp/id_coachbot_proxy.pub >> \
           /home/coachbot_proxy/.ssh/authorized_keys"
   done
   export MY_PASS=""

We need to ensure the Coachbots can ``ssh`` proxy into the **cctld** machine,
so you should do something like:

.. code-block:: bash

   export PROXY_USER=coachbot_proxy
   cctl exec --bots=90-99 "ssh -o \"StrictHostKeyChecking=no\" \
       $PROXY_USER@192.168.1.2 'exit'"

When you're done with that, let us setup the proxy settings for **apt-get** on
the coachbots:

.. code-block:: bash

   cctl exec --bots=90-99 "echo pi | sudo -S sh -c \
      'echo Acquire::http::proxy\ \\\"socks5h://localhost:16899\\\"\; > \
          /etc/apt/apt.conf.d/12proxy'"

Copying SSH Keys
^^^^^^^^^^^^^^^^

If you were to SSH into the Coachbots, you would need to provide either an ssh
key or a password. `Providing passwords is inherently difficult to securely
achieve` and **cctl does not support password-based ssh authentication**.
Consequently, you need to copy your ssh public id to all the coachbots.
**Assuming you have a coachbot key you can use**, this task is as trivial as
running:

.. code-block:: bash

   # You can use the -n flag with ssh-copy-id for a dry run.
   for i in {3..102}; do \
       echo "Installing key to 192.168.1.$i."; \
       sshpass -p YOUR_PASSWORD -v \
           ssh-copy-id -i path/to/id_coachbot.pub "pi@192.168.1.$i"; \
   done

.. warning:: Never run this command without the ``-i`` flag. If you run the
   command without the ``-i`` flag, you will copy over all your ssh keys which
   may potentially be leaking access to the coachbots depending on how
   protected those ssh keys are.

.. note:: You can run ``ssh-copy-id`` with the ``-n`` flag to perform a dry run
   and check if everything behaves as expected before actually adding the key.

.. note:: You may encounter that this snippet will ask you about the known
   hosts for a 100 times or sshpass reporting issues with strict host checking.
   You can skip these checks with ``-o "StrictHostKeyChecking=no"`` given to
   ``ssh-copy-id``. You should, however, ensure that the IP addresses you are
   connecting to are correct. 

When you're done with that, you can simply run:

.. code-block:: bash

   for i in {3..102}; do \
       echo -n "192.168.1.$i: "; \
       ssh pi@192.168.1.$i 'echo "Successfully Connected."'; \
   done

to check if everything went as expected. You should get a printout of all
coachbots reporting a successful connection.

Udev Rules
^^^^^^^^^^

We must create some new udev rules in order for the daughterboards to create
correct Linux devices. To do this, you can simply edit
``/etc/udev/rules.d/72-cctl-daughters.rules`` (create if it doesn't exist) to
look like:

.. code-block:: text

   SUBSYSTEM=="tty" ATTRS{manufacturer}=="Arduino*" \
   ATTRS{serial}=="<YOUR_SERIAL>" SYMLINK+="cctl-arduino"

To find the serial number, you can run ``udevadm info -a -n /dev/ttyACM<X>``
where ``<X>`` is the number that you are certain the Arduino is on.

You can plug out and then plug back in the Arduino daughterboard.

Now that you've done this, you are guaranteed to have ``/dev/cctl-arduino`` as
a file (as a symlink to  ``/dev/ttyACM*``).

Configuration Files
^^^^^^^^^^^^^^^^^^^

**cctl** exposes some configuration files that you can use to tweak its
behavior. These configuration files are normally located either in
``~/.config/coachswarm/`` or ``/etc/coachswarm/``.

.. note:: **cctl** reads ``~/.config/coachswarm/`` configuration files first
   and falls back to ``/etc/coachswarm/`` files if those do not exist. If
   **cctl** is unable to find either of these files, it will automatically
   generate new files in ``~/.config/coachswarm/{cctl,coachswarm}.conf`` with
   sane defaults.

From now, the term ``$CONFDIR`` refers to the loaded configuration directory as
described. In ``$CONFDIR`` two configuration files are supported.

cctl.conf
^^^^^^^^^

The ``$CONFDIR/cctl.conf`` file configures **cctl**’s behavior. The following
is an example file with all supported keys.

.. code-block:: ini
   :caption: cctl.conf

   [server]
   # The interface controlling the Coachbots. This is the interface that is
   # connected to the same network as the Coachbots.
   interface = enp60s0
   
   # The fully qualified path to the legacy server directory.
   path = /home/hanlin/coach/server_beta
   
   [coachswarm]
   # The fully qualified path to the coachswarm.conf file. This file is legacy
   # code but is fully necessary in running the coachswarm. The file specified
   # here will be used to control the coachbots.
   conf_path = /home/marko/.config/coachswarm/coachswarm.conf

   # The user running on the Coachbots.
   ssh_user = pi
   # This is the path to the private ssh-key that you just registered with all
   # the coachbots.
   ssh_key = /home/marko/.ssh/id_coachbot
   
   # These two configuration parameters specify the minimum and maximum ID of
   # the coachbots. id_range_min is the smallest ID in the coachswarm while
   # id_range_max is the biggest ID of the coachswarm.
   id_range_min = 0
   id_range_max = 99
   
   [camera]
   # The name of the raw device to be used as the input video stream. You can
   # find this with `cat /sys/class/video4linux/video*/name` of the appropriate
   # video* number.
   raw_dev_name = Piwebcam: UVC Camera
   
   # The name of the output processed video stream. This can be arbitrary, but
   # note that the resulting video stream generated by `cctl cam setup` will be
   # named however you named it here.
   processed_dev_name = Coachcam: Stream_Processed
   
   # Lens correction parameters. These are to be experimentally determined.
   # cx is the x-coordinate focal center offset relative to the frame center.
   # cy is the y-coordinate equivalent.
   k1 = -0.22
   k2 = -0.022
   cx = 0.52
   cy = 0.5

   [logs]
   # The path to the local and remote syslog file.
   syslog_path = /var/log/syslog
   # The legacy log file path. This file is the file that used to be fetched
   # with ./collect_data.py and ./harvest.py
   legacy_log_file_path = /home/pi/control/experiment_log

   [arduino-daughter]
   # The port the arduino daughterboard is connected to.
   port = /dev/ttyACM0
   # The communication baudrate
   baudrate = 115200
   # The fully qualified board name of the daughterboard
   board = arduino:avr:uno
   # The arduino-cli executable path
   arduino-executable = /usr/local/bin/arduino-cli

Configuring **cctld**
^^^^^^^^^^^^^^^^^^^^^

You are required to configure **cctld** in order to achieve commuincation
between the coachbots and it. The configuration file should be stored in
``/etc/coachswarm/cctld.conf`` and **cctld** will attempt to read from it. If
this file does not exist, **cctld** will **not start**. The format of the file
is:

.. include:: ../../src/static/cctld.conf
   :code: ini
   :name: cctld.conf
   
Systemd Service
~~~~~~~~~~~~~~~

To get **cctld** to be a proper Linux service we have many options. We could
put a script in ``/etc/init.d/`` (and if you are more familiar with that you
are more than welcome to). However, I personally prefer to use
**systemd** [#fsystemd]_. To do this, we need to make a simple file to let
**systemd** know about **cctld** and let it manage it as a proper service.
Something along the lines of the following should work.

.. include:: ../../src/static/cctld.service
    :code:
    :name: /etc/systemd/system/cctld.service

Then you can tell **systemd** to enable this service on boot and immediately
start it:

.. code-block:: bash

   sudo systemctl enable cctld
   sudo systemctl start cctld

The next time your computer boots up, **cctld** will start automatically. You
don't even need to log in.

When you're done configuring **cctl**, you can visit `Usage <usage.html>`_ for
information on how to effectively use **cctl**.

.. rubric:: Footnotes

.. [#fsystemd] I know that **systemd** has its flaws and that it is not the
   prefered tool of many users. **cctld** is written as daemon and not as a
   **systemd** service for this very reason. You are by no means obliged to use
   **systemd** if you are a fan of traditional service management.
