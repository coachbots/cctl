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
