Installation
============

Installing **cctl** is a task of fetching all its dependencies, building it and
installing it. Because, at this moment, we do not ship Debian packages, you
must manually build **cctl** yourself.

Dependencies
------------

Before installing **cctl** ensure you have ``ffmpeg``, ``v4l2loopback``,
``vlc``, ``python3.8``, ``pandoc`` and the appropriate ``pip`` version.

You also need to have ``arduino-cli`` installed.

Then, install the ``arduino:avr`` toolchain with ``arduino-cli core install
arduino:avr``.

Alongside this, ``cctl`` depends on ``bluepy``, ``pyzmq``, ``pyserial``,
``reactivex`` and ``python-daemon``.

Distro-specific Guides
----------------------

Ubuntu
^^^^^^

On Ubuntu, you can install all of the system dependencies with:

.. code-block:: bash

   sudo apt-get install -y ffmpeg python3.8 v4l2loopback-dkms pandoc \
       libglib2.0-dev, vlc
   sudo curl -fsSL \
       https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
       | BINDIR=/usr/local/bin sh
   sudo arduino-cli core install arduino:avr

You can then install the required python dependencies via ``pip``:

.. warning::

   The following section is tentative. You should not be installing packages
   via ``pip`` if they are packaged as system packages. Only do this if you
   know what you are doing and are ready to face the consequences of a messy
   system.

.. code-block:: bash

   sudo python3.8 -m pip install pyzmq pyserial reactivex bluepy \
       python-daemon numpy


The task of installation is then simply cloning the repository, building it and
installing all of the required files.

.. code-block:: bash

   git clone git@github.com:coachbots/cctl.git
   cd cctl
   make
   sudo make install

.. include:: configuration.rst
