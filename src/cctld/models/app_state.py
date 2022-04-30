#!/usr/bin/env python

"""This module defines the ``AppState`` class holding the full application
state."""


from dataclasses import dataclass
from reactivex.subject import BehaviorSubject


@dataclass
class AppState:
    """This class holds the full application state."""
    coachbot_states: BehaviorSubject
