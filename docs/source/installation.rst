Installation
============

Installing **cctl** is a task of fetching all its dependencies, building it and
installing it. Because, at this moment, we do not ship Debian packages, you
must manually build **cctl** yourself.

Dependencies
------------

Before installing **cctl** ensure you have ``ffmpeg``, ``v4l2loopback``,
``python3.6``, ``pandoc`` and the appropriate ``pip`` version.

Distro-specific Guides
----------------------

Ubuntu
^^^^^^

On Ubuntu, you can install all of the dependencies with:

.. code-block:: bash

   sudo apt-get install ffmpeg python3.6 v4l2loopback-dkms pandoc
   pip install --user build

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

   for bot in {93..102}; do
       ssh pi@192.168.1.$bot \
           "ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_coachbot_proxy"
       ssh pi@192.168.1.$bot "cat ~/.ssh/id_coachbot_proxy.pub" | \
           cat > /tmp/id_coachbot_proxy.pub
       echo <COACHBOT-PROXY-PASS> | sudo -S -u coachbot_proxy sh -c \
           "mkdir -p /home/coachbot_proxy/.ssh; \
           cat /tmp/id_coachbot_proxy.pub >> \
           /home/coachbot_proxy/.ssh/authorized_keys"
   done
