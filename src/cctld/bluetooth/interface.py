# -*- coding: utf-8 -*-

"""This module contains the code that initializes all bluetooth interfaces that
are available, creates a Queue for them."""


import os
from subprocess import check_output
from typing import List, Optional, Tuple
from queue import Queue

from cctld import bluetooth


class Interface:
    def __init__(self, id: int) -> None:
        self.id = id


class Interfaces:
    """This class exposes the interfaces that are usable by the bluetooth."""
    @staticmethod
    def get_all() -> List[Interface]:
        hci = check_output(['hciconfig'], universal_newlines=True).split('hci')
        host_ids = [int(list(hci[i])[0]) for i in range(1, len(hci))]
        return [Interface(id) for id in host_ids]

    def __init__(self) -> None:
        self._interfaces = Interfaces.get_all()
        self._queues = [Queue() for _ in self._interfaces]

    @property
    def interfaces_and_queues(self) -> List[Tuple[Interface, Queue]]:
        """Returns the list of interface-queue pairs."""
        return list(zip(self._interfaces, self._queues))

    def get_free(self) -> Optional[Interface]:
        """Returns an interface currently available for work. This function may
        return None if there is no free interface.
        """
        for i, q in self.interfaces_and_queues:
            if q.empty():
                return i

        return None

    def add_task(self, task: bluetooth.Task):
        min_q = self.interfaces_and_queues[0][1]

        for _, q in self.interfaces_and_queues:
            # TODO: Possibly qsize is not the best option here, but, it's a
            # cheap devtime implementation.
            if q.qsize() < min_q.qsize():
                min_q = q

        min_q.put(task)
