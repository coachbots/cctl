#!/usr/bin/env python

"""This module defines the ``AppState`` class holding the full application
state."""


from typing import Tuple
from dataclasses import dataclass
from cctl.models.coachbot import CoachbotState
from reactivex.subject import BehaviorSubject
from cctld.conf import Config


@dataclass
class AppState:
    """This class holds the full application state.

    Attributes:
        coachbot_states: Holds the current state of the Coachbots.
        config: Holds the current application configuration.
    """
    coachbot_states: BehaviorSubject[Tuple[CoachbotState, ...]]
    config: Config
