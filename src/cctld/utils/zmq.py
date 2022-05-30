#!/usr/bin/env python

"""This module exposes some helpful zmq-related network utilities."""

import zmq
import zmq.asyncio


async def zmq_create_poller(*args: zmq.asyncio.Socket) -> zmq.asyncio.Poller:
    """Creates a poller and registers all sockets passed as arguments."""
    poller = zmq.asyncio.Poller()
    for sock in args:
        poller.register(sock, zmq.POLLIN)
    return poller


async def async_proxy(frontend: zmq.asyncio.Socket,
                      backend: zmq.asyncio.Socket) -> None:
    """Mimicks the behavior of ``zmq.proxy`` but for ``asyncio``."""
    poller = await zmq_create_poller(frontend, backend)

    while True:
        socks = dict(await poller.poll())

        if socks.get(frontend) == zmq.POLLIN:
            request_raw = await frontend.recv_multipart()
            await backend.send_multipart(request_raw)

        if socks.get(backend) == zmq.POLLIN:
            request_raw = await backend.recv_multipart()
            await frontend.send_multipart(request_raw)
