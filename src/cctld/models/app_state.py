#!/usr/bin/env python

"""This module defines the ``AppState`` class holding the full application
state."""


from typing import Tuple
from dataclasses import dataclass
from cctl.models.coachbot import Coachbot, CoachbotState
from reactivex.subject import Subject, BehaviorSubject


@dataclass
class AppState:
    """This class holds the full application state.

    Attributes:
        coachbot_states: Holds the current state of the Coachbots.
        requested_states: Holds the requested states.
    """
    coachbot_states: BehaviorSubject[Tuple[CoachbotState, ...]]
    requested_states: Subject[Coachbot]
