Low-Level Language-Agnostic API
-------------------------------

It is indeed possible to access **cctld** via any language, as long as it
supports `ZMQ <https://zeromq.org/>`__. ZMQ is a hard dependency and we do not
plan on migrating away from it.

To query **cctld** in your prefered language, you must adhere to the protocol
that has been described in section 

.. code-block:: guess

   #include <string.h>
   #include <zmq.h>
   // ...
   void* zmq_ctx = zmq_ctx_new();
   void* sock = zmq_socket(zmq_ctx, ZMQ_REQ);

   char my_req[] = "{"
       "\"method\": \"read\","
       "\"endpoint\": \"/bots/state/1\","
       "\"head\": {},"
       "\"body\": \"\""
   "}";

   char recv_buffer[128];
   zmq_connect(sock, "ipc:///var/run/cctld/request_pipe");
   zmq_send(sock, my_req, sizeof(my_req), 0);
   zmq_recv(sock, recv_buffer, 128, 0);

   // This should evaluate to true.
   assert strcmp(recv_buffer, "{ \"result_code\": 200, \"body\": \"\" }") == 0;
   // ...
