Protocols
=========

Request-Response
----------------

The Request-Reponse API protocol revolves around the models defined in the 
`cctl.protocol.ipc <api_modules.html#module-cctl.protocols.ipc>`__ module.When
attempting to query the data in the Request-Response API (from now on -- RR
API) you must strictly adhere to these protocols or **cctld** will simply deny
and ignore your requests.

Requests
^^^^^^^^

All of your requests must be `JSON <https://www.json.org>`__ objects and must
at the bare minimum adhere to the schema:

.. jsonschema:: schemas/ipc-request.json

.. warning::

   The body is indeed a string and not an object itself. If you wish to pass an
   object, you must manually serialize it to JSON and deserialize it yourself,
   depending on the request.

You might notice if you are familiar with HTTP that this is oddly familiar to
HTTP. I chose not to reinvent the wheel too much so I opted for something that
is familiar to most people and that most people would find quick and easy to
use.

You will also notice that the ``method`` field only accepts values of
``create``, ``update``, ``read``, ``delete``. This is due to the desire to
adhere to `CRUD
<https://en.wikipedia.org/wiki/Create,_read,_update_and_delete>`__ (perhaps too
literally) so that you can expect requests to behave as almost all
request-based services do.

Responses
^^^^^^^^^

Upon a valid request targetted at a valid endpoint, **cctld** will reply with a
JSON-serialized `cctl.protocol.ipc.Response
<api_modules.html#cctl.protocols.ipc.Response>`__ that will adhere to the
schema:

.. jsonschema:: schemas/ipc-response.json

As one can see, the ``result_code``'s that **cctld** will return are very
similar to HTTP error codes and are to be interpreted as HTTP error codes are.
See the `MDN Article
<https://developer.mozilla.org/en-US/docs/Web/HTTP/Status>`__ for useful
information on what these numbers mean.

API Endpoints
^^^^^^^^^^^^^

With the basics out of the way, let's get to making fun requests. As you've
seen, each request must have an ``endpoint`` field. This ``endpoint`` will then
call the relevant handler on ``cctld``. These are similar to `REST API
<https://www.redhat.com/en/topics/api/what-is-a-rest-api>`_'s and mimic their
behavior. All requests are stateless.

**read** /teapot
~~~~~~~~~~~~~~~~

Unconditionally returns a ``418`` response.

**Returns**: 418

.. code-block:: text

   REQUEST: {
     "endpoint": "/teapot",
     "method": "read",
     "head": {},
     "body": ""
   }

   RESPONSE: {
     "result_code": 418,
     "body": ""
   }

**read** /bots/(id: int)/state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns the current state of the coachbot.

**Returns**: 200

.. code-block:: text

   REQUEST: {
     "endpoint": /bots/90/state
     "method": "read",
     "head": {},
     "body": ""
   }

   RESPONSE: {
     "result_code": 200,
     "body": "{
       \"is_on\": true,
       \"os_version\": \"1.0.0\",
       \"bat_voltage\": 3.8,
       \"position\": null,
       \"theta\": null,
       \"user_code_state\": {
         \"is_running\": false,
         \"version\": null,
         \"name\": null,
         \"author\": null,
         \"requires_version\": null,
         \"user_code\": null
       }
     }"
   }

In this example the state of the coachbot is only known to be `booted on`, with
an `os-version` of `1.0.0` and a battery voltage of `3.8`. The other values
being `null` means that `cctld` does not know more information about the
coachbot `90`.

**create** /bots/(id: int)/user-code/running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Turns on the user code.

**Returns**: 200, 409

.. code-block:: text

   REQUEST: {
     "endpoint": /bots/90/user-code/running
     "method": "create",
     "head": {},
     "body": ""
   }

   RESPONSE: {
     "result_code": 200,
     "body": "":
   }

In this example **cctld** managed to start the user code if it was not started
before or the user code is already running so no changes were necessary.

A response code of `409` indicates that the Coachbot is not turned on so it is
not possible to change the state of the user code.


**delete** /bots/(id: int)/user-code/running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Turns off the user code.

**Returns**: 200, 409

.. code-block:: text

   REQUEST: {
     "endpoint": /bots/90/user-code/running
     "method": "delete",
     "head": {},
     "body": ""
   }

   RESPONSE: {
     "result_code": 200,
     "body": "":
   }

In this example **cctld** managed to stop the user code if it was not started
before or the user code is already stopped so no changes were necessary.

A response code of `409` indicates that the Coachbot is not turned on so it is
not possible to change the state of the user code.


**update** /bots/(id: int)/user-code/code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Updates the user code.

**Returns**: 200, 409

.. code-block:: text

   REQUEST: {
     "endpoint": /bots/90/user-code/running
     "method": "delete",
     "head": {},
     "body": "def usr(bot):\n    while True:\n    bot.set_led(10, 10, 10)\n"
   }

   RESPONSE: {
     "result_code": 200,
     "body": "":
   }

In this example, the bot was successfully updated.

A response code of `409` indicates that the Coachbot is not turned on so it is
not possible to change the state of the user code.


Schemas
^^^^^^^

These are the schemas that are used in the API endpoints.

.. jsonschema:: schemas/ipc-bot-state.json

.. jsonschema:: schemas/ipc-user-code-state.json
