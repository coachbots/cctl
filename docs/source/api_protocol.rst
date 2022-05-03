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

With the basics out of the way, let's get to making fun requests.
