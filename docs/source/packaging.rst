Packaging
=========

In order to finally deploy **cctl** you must package it. This packaging process
depends on your machine and your goals. If you wish to package for
Ubuntu/Debian, then you must do so on a Debian-based machine. Similarly goes
for an RPM-based machine.

Debian (and Ubuntu)
-------------------

To successfully package for Debian, you can simply use the provided
``Makefile``. Your best bet is to do something along the lines of:

.. code-block:: bash
   
   sudo apt install python3-stdeb
   git clone https://github.com/coachswarm/cctl
   cd cctl
   make prepare-deb
