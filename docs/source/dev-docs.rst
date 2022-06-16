Developer Documentation
=======================

In this document, I'll try to outline how you can start developing for **cctl**
and **cctld**. The architecture has become quite large, so I would recommend
reading this before attempting to hack around in **cctl** and **cctld**.

I will attempt to guide this process with an example. Suppose we would like to
implement a new feature which `fetches a very specific file from the bots`.
Likely, this feature does not need to exist in the real world (since you can
simply ``ssh``), but let us make-pretend no file-transfer protocol exists for
the sake of the example.

Developing in General
---------------------

Recall the general architecture of the system. In this architecture we have
three packages that we need to tackle: ``coach_os``, ``cctld`` and
``cctl.api``. We may possibly add a ``cli`` hook for our example too.

Developing for **coach-os**
---------------------------

Currently, **coach-os** is still in disarray. You are on your own.

.. warning::

   TODO: FIXME

Developing for **cctld**
-----------------------

When you managed to implement your feature on **coach-os**, we must now work on
adding that feature to **cctld**.

Architecture
^^^^^^^^^^^^

The architecture of **cctld** revolves around Observable objects. If you are
unfamiliar with this, I would recommend taking a look at `ReactiveX
<https://reactivex.io/>`__ which is the backbone of **cctld**.

**cctld** is comprised of a central ``AppState`` and some ``async`` servers
which handle the various functionalities **cctld** has. The whole system works
in one ``async`` event loop, meaning there are no threading/concurrency hassles
to deal with.

The architecture of **cctld** follows:

.. graphviz::
   :align: center

   digraph {
       {
           node [shape=ellipse] botstates [label="Bot States"]
           node [shape=ellipse] signals [label="Bot Signals"]
           node [shape=diamond] arduino [label="Arduino"]
           node [shape=cylinder] statuss [label="Status"]
           node [shape=cylinder] reqs [label="Request"]
           node [shape=cylinder] feeds [label="Feed"]
           node [shape=cylinder] sigs [label="Signal"]
       }
       subgraph cluster_appstate {
           botstates; signals; arduino;
           label="AppState";
           graph[style=dotted];
       }
       subgraph cluster_servers {
           statuss; reqs; feeds; sigs;
           label="Servers";
           graph[style=dotted];
       }
       botstates -> feeds [color=green];
       signals -> sigs [color=green];

       statuss -> botstates [color=blue];
       statuss -> signals [color=blue];

       arduino -> reqs [color=red];
       botstates -> reqs [color=red];
   }

To make some sense of that, check out this legend:

.. graphviz::
   :align: center

   digraph {
       compound=true;
       rankdir=TB

       subgraph cluster_legend {
           graph [style=invis];
           node [shape=ellipse] lsubject [label="Subject"];
           node [shape=diamond] lobject [label="POJO"];
           node [shape=cylinder] lserver [label="Server"];
       }

       subgraph cluster_legend2 {
           graph [style=invis];
           node [shape=ellipse] a [label="A"];
           node [shape=cylinder] b [label="B"];
           a -> b [color=green, label="Observes"];
           b -> a [color=blue, label="Provides"];
           a -> b [color=red, label="Reads"];
       }

       edge [style=invis];
       lobject -> a [ltail=cluster_legend, lhead=cluster_legend2];
   }


All application data is encapsulated in a ``cctld.models.AppState`` object. The
app state has a total of four members that it handles (configuration values are
hidden away in this graph for the sake of clarity -- every server reads from
them). Then, four servers are instantiated which have various relations to the
appstate and its members. There are three total relations that we must be vary
off when handling the app state. These relations are:

* Reading: In English: `B reads a value (from) A`, `B reads the value of A`.
* Observing: In English: `B tracks for changes in A and acts accordingly`, `B
  observes A`.
* Providing: In English `B puts new values into A`, `B calls the on_next in A`.

The arrows are directed in the direction of dataflow, hence the discrepancy
between English and the graph.

Servers
^^^^^^^

Now that you're familiar with how things glue together, let's take a brief look
at what the actual servers are and what their purpose is.

Under the hood, all servers are based on `ZMQ <https://zeromq.org/>`__-style
sockets.

Signal Server
~~~~~~~~~~~~~

The `signal server
<cctld.html#cctld.servers.start_ipc_signal_forward_server>`__ is a server that
establishes a ``PUBLISH`` - ``SUBSCRIBE`` connection to a client such that
whenever ``coach-os`` emits a signal, the signal gets passed through to all
subscribed clients. A visualization of that is:

.. graphviz::
   :align: center

   digraph {
       {
           node [style=filled] cb1 [label="Coachbot 1 Signal"]
           node [shape=cylinder] cctld [label="Signal Server"]
           node [shape=box] cctl1
               [label="cctl.api.cctld.CCTLDSignalObservable"]
           node [shape=box] cctl2
               [label="cctl.api.cctld.CCTLDSignalObservable"]
       }

       cb1 -> cctld [label="Signal"];
       cctld -> cctl1 [label="Signal"];
       cctld -> cctl2 [label="Signal"];
   }

This server should be relatively self-explanatory in the source code, so there
is little explanation that needs to be done.

Feed Server
~~~~~~~~~~~

The `feed server <cctld.html#cctld.servers.start_ipc_feed_server>`__ is another
``PUBLISH`` - ``SUBSCRIBE`` server that exposes the coachbot state data to
listener APIs. As the coachbot state data changes, so will this server forward
those changes over the transport to listener APIs.

.. graphviz::
   :align: center

   digraph {
       {
           node [style=filled] cb1 [label="Coachbot"]
           node [shape=cylinder] cctld [label="Feed Server"]
           node [shape=box] cctl1
               [label="cctl.api.cctld.CCTLDCoachbotStateObservable"]
       }

       cb1 -> cctld [label="New State"];
       cctld -> cctl1 [label="Set of all 100 updated states"];
   }

This server should be relatively self-explanatory in the source code, so there
is little explanation that needs to be done.

Status Server
~~~~~~~~~~~~~

The `status server <cctld.html#cctld.servers.start_status_server>`__ is a
``RESPONSE`` server that listens for requests made by the coachbots to update
their state or send signals. Its main purpose is to handle these requests
quickly and push this data to the observables, letting the other servers handle
what to do from there.

The server is operation is quite trivial. Upon the receival of a
`status.Request <cctl.protocols.html#cctl.protocols.status.Request>`__, this
server parses it and calls the ``on_next`` on the appropriate
``reactivex.Subject``'s.

Request Server
~~~~~~~~~~~~~~

This server is the main meat of **cctld**'s server set as it is the server than
practically enables full control of the swarm. It is another ``RESPONSE``
server that listens for requests, however, these requests are from **cctl**
clients. Unlike the previous servers, its operation is quite non-trivial.

If you are already not familiar with the `ipc.Request
<api_protocol.html#ipc-request>`__ protocol, please take a look at it. It is
important that you are familiar with the protocol. The endpoint value will be
handled by an appropriate handler, if it is hooked for the given method. In
vague terms, the operation is as follows.

.. graphviz::
   :align: center

   digraph {
       {
           node [] start [label="Receive Request"];
           node [] parse [label="Parse"];
           node [shape=diamond] checkvalid [label="Valid Method?"];
           node [shape=box] novalid [label="BAD_REQUEST 400"];
           node [shape=diamond] findhandler [label="Find Handler?"]
           node [shape=box] nohandler [label="NOT_FOUND 404"]
           node [shape=ellipse] handler [label="Handler"];
           node [shape=box] response [label="Response"];
       }

       start -> parse;
       parse -> checkvalid;
       checkvalid -> novalid [label="No"];
       checkvalid -> findhandler [label="Yes"];
       findhandler -> nohandler [label="No"];
       findhandler -> handler [label="Yes"];
       handler -> response;
   }

However, it is curious how finding handlers actually operates. The
`cctld.requests.handler.handler
<cctld.requests.html#cctld.requests.handler.handler>`__ function is responsible
for transforming methods into functions, while the `cctld.requests.handler.get
<cctld.requests.html#cctld.requests.handler.handler>`__ function is responsible
for finding handlers that have been registered. The `get` function is exactly
the handler finding function in the previous chart.

What all this means is that if you want to add another handler into **cctld**,
it's as easy as doing:

.. code-block:: python

   from cctl.protocls import cctl
   from cctl.requests import handler

   @handler('/endpoint_regex/?$', 'create')
   def my_function(app_state, request, regex_matches) -> ipc.Response:
       return ipc.Response(ipc.ResultCode.OK)

Now, this handler will get invoked for an ``ipc.Request`` of the following
form:

.. code-block:: json

   {
       "endpoint": "/endpoint_regex",
       "method": "create",
       "head": {},
       "body": ""
   }

and also:

.. code-block:: json

   {
       "endpoint": "/endpoint_regex/",
       "method": "create",
       "head": {},
       "body": ""
   }

Your handler has full access to the app state and you can use it however you
see fit. And actually, the way this is implemented is that whereever you define
this function, it will get registered as long as the decorator is used.
Currently-defined handlers live in the ``cctld.requests.__init__`` package, so
the ones you write should probably be there too.

The regex-based matching enables you to make endpoints with numbers in them
too, and the third parameter of your handler will receive the regex matches, so
you could make a handler like so:

.. code-block:: python

   @handler(r'^/bots/([0-9]+)/state/is-on/?$', 'create')
   async def create_bot_is_on(
       app_state: AppState,
       _: ipc.Request,
       endpoint_groups: Tuple[Union[str, Any], ...],
   ):
       """Turns a bot on."""
       bot = Coachbot((ident := int(endpoint_groups[0])),
                      app_state.coachbot_states.value[ident])

       # Turn on bot here.

       return ipc.Response(ipc.ResultCode.OK)

So then all of these would be valid requests:

.. code-block:: json

   { "endpoint": "/bots/1/state/is-on/", "method": "create", "head": {}, "body": "" }
   { "endpoint": "/bots/1/state/is-on", "method": "create", "head": {}, "body": "" }
   { "endpoint": "/bots/83/state/is-on", "method": "create", "head": {}, "body": "" }
   { "endpoint": "/bots/123/state/is-on", "method": "create", "head": {}, "body": "" }

Messaging Coachbots
^^^^^^^^^^^^^^^^^^^

So far we've only described how coachbots provide their state to **cctld**, but
**cctld** can do so much more -- after all, it can send commands to
**coach-os**. This is done throught the client available in `coach_commands
<cctld.html#module-cctld.coach_commands>`__. This is a simple ``REQUEST``
client that you can use to make requests to **coach-os**. It is invoked as
follows:

.. code-block:: python

   async with CoachCommand(host, port) as client:
       client.set_led_color((100, 0, 0))

You can extend the command client by adding your own function. See how
`set_user_code <cctld.html#cctld.coach_commands.CoachCommand.set_user_code>`__
is implemented for an example.

Controlling Bluetooth
^^^^^^^^^^^^^^^^^^^^^

TODO

Controlling the Arduino Daughterboard
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO

Controlling the Camera
^^^^^^^^^^^^^^^^^^^^^^

TODO

To tie in to our example, then, in order for us to make the request to
**coach-os** to provide is with a file, we would need to make a
``CoachCommand``, however, in order to expose this to the API, we would also
need to define it in ``cctld.requests.__init__.py``. Let's do that first.

.. code-block:: python
   :caption: cctld/requests/__init__.py

   # ...

   @handler(r'^/bots/([0-9]+)/secret-file/?$', 'read')
   async def read_bot_secret_file(app_state, request, endpoint_groups):
       # Let us build the bot object.
       bot = Coachbot((ident := int(endpoint_groups[0])),
                      app_state.coachbot_states.value[ident])

       # Fetch the password from the request body
       password = request.body

       # Get the configuration port.
       port = app_state.config.coach_client.command_port

       try:
           # Make the command.
           async with CoachCommand(bot.ip_address, port) as cmd:
               my_file = await cmd.fetch_secret_file(password)
           if my_file is None:
               # Not the right response code, but you should not use 403
               # here because that is reserved for future use.
               return ipc.Response(ipc.ResultCode.STATE_CONFLICT)

           # Let's return an OK response with the file contents.
           return ipc.Response(ipc.ResultCode.OK, my_file)
       except CoachCommandError as c_err:
           return ipc.Response(ipc.ResultCode.INTERNAL_SERVER_ERROR, str(cerr))

Now we need to make a new method for ``CoachCommand`` that actually fetches
this file, so let's do that too:

.. code-block:: python
   :caption: cctld/coach_commands.py

   # ...

   async def fetch_secret_file(self, password: str) -> str:
        msg = coach_command.Request(
            'read'
            '/secret-file'
        ).to_dict()

        async def worker(sock: zmq.asyncio.Socket):
            await sock.send_json(msg)
        return await self._execute_socket(worker)

So, with all that done, when the client makes a request to
``/bots/<BOT-ID>/secret-file`` with the file password as the body, **cctld**
will end up calling the ``read_bot_secret_file`` function, which will then make
a ``CoachCommand`` request, which will then ask the robots for info who will
then reply with the file. It was that easy!
