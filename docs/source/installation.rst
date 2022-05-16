Installation
============

Installing **cctl** is a task of fetching all its dependencies, building it and
installing it. Because, at this moment, we do not ship Debian packages, you
must manually build **cctl** yourself.

Dependencies
------------

Before installing **cctl** ensure you have ``ffmpeg``, ``v4l2loopback``,
``python3.6``, ``pandoc`` and the appropriate ``pip`` version.

You also need to have ``arduino-cli`` installed. To do this, you should run
this in a root shell:

.. code-block:: bash

   curl -fsSL \
       https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
       | BINDIR=/usr/local/bin sh

Then, install the ``arduino:avr`` toolchain with ``arduino-cli core install
arduino:avr``.

Alongside this, ``cctl`` depends on ``bluepy``, ``importlib-resources`` and
``python-daemon``.

Distro-specific Guides
----------------------

Ubuntu
^^^^^^

On Ubuntu, you can install all of the dependencies with:

.. code-block:: bash

   sudo apt-get install ffmpeg python3.6 v4l2loopback-dkms pandoc \
       libglib2.0-dev
   pip install --user build bluepy python-daemon

The task of installation is then simply cloning the repository, building it and
installing all of the required files.

.. code-block:: bash

   git clone git@github.com:markovejnovic/cctl.git
   cd cctl
   make
   sudo make install

When you're done installing **cctl** see the `Configuration
<cofiguration.html>`_ for information on configuring it.

Setting up a Proxy User
^^^^^^^^^^^^^^^^^^^^^^^

**cctl** also requires a specific user it can use to setup secure proxying
between **coach-os** and itself. You can create this user by running:

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

We need to ensure the Coachbots can ``ssh`` proxy into the **cctl** machine,
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
