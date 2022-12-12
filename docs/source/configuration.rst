Configuration
-------------

**cctl** requires some minor manual configuration to be done before you can
fully use it.

Setting Up The CCTLD User
^^^^^^^^^^^^^^^^^^^^^^^^^

**cctld** should not be run as root. Besides being insecure, it will not work.
We are best off creating a **cctld** user. It will need the **video** and
**dialout** group permissions so we can do the following:

.. code-block:: bash

   sudo useradd -r -s /bin/false cctld  # Ban it from logging in.
   sudo adduser cctld video  # Required to communicate with the video stream
   sudo adduser cctld dialout  # Required to communicate with the arduino
   sudo adduser cctld bluetooth  # Required to communicate with the bluetooth
                                 # interfaces.


.. warning::

   This assumes that there exists a ``bluetooth`` group with permissions to
   access the bluetooth interface (default on Ubuntu). If this group does not
   exist, you must create it and add the D-Bus permissions:

   .. code-block:: bash

      groupadd bluetooth
      sudo nano /etc/dbus-1/system.d/bluetooth.conf

   Then, in that file, you are to add the following policy:

   .. code-block:: xml

      <policy group="bluetooth">
        <allow send_destination="org.bluez"/>
        <allow send_interface="org.bluez.Agent1"/>
        <allow send_interface="org.bluez.GattCharacteristic1"/>
        <allow send_interface="org.bluez.GattDescriptor1"/>
        <allow send_interface="org.freedesktop.DBus.ObjectManager"/>
        <allow send_interface="org.freedesktop.DBus.Properties"/>
        <allow send_interface="org.freedesktop.DBus.Properties"/>
      </policy>

   After you do this, then you can do ``sudo adduser cctld bluetooth``.

You will also need to give ``cctld`` the permissions to reset
``bluetooth.service`` via ``sudoedit /etc/sudoers``:

.. code-block:: bash

   # Dump this at the bottom:
   Cmnd_Alias CCTLD_COMMANDS = /bin/systemctl restart bluetooth
   cctld   ALL=(ALL) NOPASSWD: CCTLD_COMMANDS

Setting up a Proxy User
^^^^^^^^^^^^^^^^^^^^^^^

**cctld** requires a specific user it can use to setup secure proxying between **coach-os** and itself. You can create this user by running:

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
``/etc/udev/rules.d/72-cctl.rules`` (create if it doesn't exist) to
look like:

.. code-block:: text

   # Create a symlink from the rail arduino to /dev/tty-cctl-arduino
   SUBSYSTEM=="tty" ATTRS{manufacturer}=="Arduino*" \
   ATTRS{serial}=="<YOUR_SERIAL>" SYMLINK+="tty-cctl-arduino"

   # Create a symlink from the Piwebcam to /dev/video-cctl-overhead-raw
   SUBSYSTEM=="video4linux" ENV{ID_MODEL_ENC}=="Piwebcam" \
   ENV{ID_MODEL}=="Piwebcam" ENV{ID_MODEL_ID}=="0104" \
   ENV{ID_SERIAL_SHORT}=="00000000be3e8505" ENV{ID_TYPE}=="video" \
   SYMLINK+="video71" \
   RUN{program}+="/sbin/modprobe v4l2loopback video_nr=72"

   # Create a processed stream whenever the arduino is connected.

To find the serial number, you can run ``udevadm info -a -n /dev/ttyACM<X>``
where ``<X>`` is the number that you are certain the Arduino is on.

You can plug out and then plug back in the Arduino daughterboard.

Now that you've done this, you are guaranteed to have ``/dev/tty-cctl-arduino``
as a file (as a symlink to  ``/dev/ttyACM*``).

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

.. include:: ../../src/cctl_static/cctl.conf
   :code: ini
   :name: cctld.conf

Configuring **cctld**
^^^^^^^^^^^^^^^^^^^^^

You are required to configure **cctld** in order to achieve commuincation
between the coachbots and it. The configuration file should be stored in
``/etc/coachswarm/cctld.conf`` and **cctld** will attempt to read from it. If
this file does not exist, **cctld** will **not start**. The format of the file
is:

.. include:: ../../src/cctl_static/cctld.conf
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

.. include:: ../../src/cctl_static/cctld.service
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
