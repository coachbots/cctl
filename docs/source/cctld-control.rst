CCTLD Control
=============

First and foremost, **cctld** is a simple daemon. It is very unopinionated in
how you administer it and you may choose to administer it however you like.

With that being said, I am familiar with ``systemd`` best, so the docs that I
provide here will be revolving around ``systemd``.

Systemd Service
---------------

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

Configuring **cctld**
---------------------

You are required to configure **cctld** in order to achieve commuincation
between the coachbots and it. The configuration file should be stored in
``/etc/coachswarm/cctld.conf`` and **cctld** will attempt to read from it. If
this file does not exist, **cctld** will **not start**. The format of the file
is:

.. include:: ../../src/cctl_static/cctld.conf
   :code: ini
   :name: cctld.conf

Upon a reconfiguration of **cctld** please run:

.. code-block:: bash

   systemctl restart cctld

to restart **cctld**.
   
Controlling **cctld**
---------------------

When **cctld** has been configured, you may simply start it and stop it with:

.. code-block:: bash

   systemctl start cctld
   # and
   systemctl stop cctld

If you would like to read **cctld** logs, you can do that with:

.. code-block:: bash

   journalctl -u cctld
   # Although you might find more utility in reversing the order with
   journalctl -ru cctld

.. rubric:: Footnotes

.. [#fsystemd] I know that **systemd** has its flaws and that it is not the
   prefered tool of many users. **cctld** is written as daemon and not as a
   **systemd** service for this very reason. You are by no means obliged to use
   **systemd** if you are a fan of traditional service management.
