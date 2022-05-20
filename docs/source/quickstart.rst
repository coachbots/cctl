Getting Started
===============

**cctl** is a system for controlling the Coachbots. It comes from a necessity
to expose Coachbot state, minimize pain when working with a swarm of robots and
generally make the experience playing with a swarm of a hundred robots
pleasant. After all, it should be!

This documentation will be a quick primer on how **cctl** and the Coachbots
work. It will get very dry at some moments and I apologize for that, but I'll
try my best to keep you entertained reading this.

Terminology
-----------

**cctl** [#fcctl]_ is written on a client-server model, meaning that there is a
centralized server which is taking care of most the heavy lifting and that
clients can connect to the server to make requests as they see fit.

The server doing the heavy lifting is called **cctld** and is the centralized
system that communicates between the coachbots and the API clients. Besides
that, it supports the coachbots, managing and tracking their state as required.
It is the only valid source of truth in real-world scenarios.

**cctl** refers to a multitude of services, but three are relevant:

1. The name **cctl** refers to the overall system and the architecture. This
   use is discouraged.
3. **cctl.api** is a Python package that enables you to communicate with
   **cctld**, query relevant information or potentially subscribe to data
   streams.
2. **cctl**, finally, refers to a CLI application that thinly wraps around
   **cctl.api** and enables you to control the coachbots through a simple
   command-line interface.

**coach-os** refers to the system that is run on the Coachbots themselves.
This, perhaps misnamed [#fcoach-os]_, package reads data from sensors and
appropriately controls the coachbots. It allows for custom user code to be run
on the coachbots, acting as an API provider, safety net and data provider for
the user code.

Architecture
------------

With this terminology described, you might benefit from a diagram showing
exactly how the architecture is laid out.

.. graphviz::
   :align: center

   digraph {
       {
           node [style=filled] cb1 [fillcolor=purple, label="Coachbot 1"]
           node [style=filled] cb2 [fillcolor=purple, label="Coachbot 2"]
           node [style=filled] cb3 [fillcolor=purple, label="Coachbot 3"]
           node [shape=box] cctld [label="cctld", fillcolor=green]
           node [shape=box] cctl1 [label="cctl.api on computer 1"]
           node [shape=box] cctl2 [label="cctl.api on computer 2"]
           node [shape=box] cctlcli [label="cctl cli"]
       }
       cb1 -> cctld [dir=both];
       cb2 -> cctld [dir=both];
       cb3 -> cctld [dir=both];

       cctld -> cctl1 [dir=both];
       cctld -> cctl2 [dir=both];

       cctl1 -> cctlcli [dir=both];
   }

This client-server architecture allows users to have full access to all the
exposed functions of **cctl** while ensuring that they will never end up
conflicting each other. Furthermore, it enables any machine that is connected
to the network to communicate through **cctl.api** with **cctld** if **cctld**
is configured to support this.

If you are now interested in using **cctl**, then you should probably visit the
`Cli Documentation <cli.html>`__ or the `API Documentation <api.html>`__.

If you would like to control **cctld**, then please check out the `CCTLD
Control <cctld-control.html>`__ documentation.

If you are trying to develop for **cctl**, you should read the `Developer
Documentation <dev-docs.html>`__ for information on existing code and possibly
helpful guidance.

.. rubric:: Footnotes

.. [#fcctl] Standing for Coachbot Control
.. [#fcoach-os] Note that **coach-os** does not integrate into the Kernel
   whatsoever. It is a purely userland piece of software.
