#!/usr/bin/env python

"""This module defines the ``AppState`` class holding the full application
state."""


from typing import Iterable, Tuple
from dataclasses import dataclass
from reactivex.subject import BehaviorSubject
from reactivex.subject.subject import Subject

from cctl.models.coachbot import CoachbotState, Signal
from cctld.daughters.arduino import ArduinoInfo
from cctld.conf import Config
from cctld import camera


class CoachbotStateSubject(Subject):
    """Implements a ZIPping State-tracking subject for the Coachbot.

    Todo:
        This implementation is really really bad and is bound to fail.
    """
    MAX_TIME_BEFORE_PRUNE = 6

    def __init__(self, bots: Iterable[CoachbotState]) -> None:
        super().__init__()
        self._internal_states = [BehaviorSubject((i, bot)) for i, bot in
                                 enumerate(bots)]
        for state in self._internal_states:
            state.subscribe(on_next=self._emit, on_completed=self._close,
                            on_error=self._close_err)

    def _emit(self, _):
        self.on_next(self.value)

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

    @property
    def tuple_value(self) -> Tuple[Tuple[int, CoachbotState], ...]:
        return tuple(state.value for state in self._internal_states)

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
    arduino_daughter: ArduinoInfo
    camera_stream: camera.ProcessingStream
