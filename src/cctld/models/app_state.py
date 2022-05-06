#!/usr/bin/env python

"""This module defines the ``AppState`` class holding the full application
state."""


from typing import Tuple
from dataclasses import dataclass
from cctld.coach_btle_client import CoachbotBTLEClientManager

from reactivex.subject.subject import Subject
from cctl.models.coachbot import CoachbotState, Signal
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
    coachbot_signals: Subject[Signal]
    coachbot_btle_manager: CoachbotBTLEClientManager
