#!/usr/bin/env python

"""This module defines the ``AppState`` class holding the full application
state."""


from typing import Iterable, Tuple, Union
from dataclasses import dataclass
import reactivex as rx
from reactivex.subject import BehaviorSubject
from reactivex.subject.subject import Subject
from reactivex import operators as rxops

from cctl.models.coachbot import CoachbotState, Signal
from cctld.coach_btle_client import CoachbotBTLEClientManager
from cctld.daughters.arduino import ArduinoInfo
from cctld.conf import Config


class CoachbotStateSubject(Subject):
    """Implements a ZIPping State-tracking subject for the Coachbot.

    Todo:
        This implementation is really really bad and is bound to fail.
    """
    MAX_TIME_BEFORE_PRUNE = 3

    def __init__(self, bots: Iterable[CoachbotState]) -> None:
        super().__init__()
        self._internal_states = [BehaviorSubject((i, bot)) for i, bot in
                                 enumerate(bots)]
        for state in self._internal_states:
            state.subscribe(on_next=self._emit, on_completed=self._close,
                            on_error=self._close_err)

        for state in self._internal_states:
            rx.zip(state, state.pipe(rxops.time_interval())) \
                .subscribe(self._prune_old)

    def _emit(self, _):
        self.on_next(self.value)

    def _prune_old(self, value: Tuple):
        if value[1].interval.total_seconds() \
                > self.__class__.MAX_TIME_BEFORE_PRUNE:
            identifier = value[0][0]
            self._internal_states[identifier].on_next(
                (identifier, CoachbotState(None)))

    def _close(self):
        for state in self._internal_states:
            state.dispose()

    def _close_err(self, error):
        for state in self._internal_states:
            state.on_error(error)
            state.dispose()

    @property
    def value(self) -> Tuple[CoachbotState, ...]:
        """Returns the currently stored value of the BehaviorSubject.

        Todo:
            Possible concurrency headache.
        """
        return tuple(state.value[1] for state in self._internal_states)

    def get_subject(self, i: int):
        return self._internal_states[i]


@dataclass
class AppState:
    """This class holds the full application state.

    Attributes:
        coachbot_states: Holds the current state of the Coachbots.
        config: Holds the current application configuration.
    """
    coachbot_states: CoachbotStateSubject
    config: Config
    coachbot_signals: Subject[Signal]
    coachbot_btle_manager: CoachbotBTLEClientManager
    arduino_daughter: ArduinoInfo
