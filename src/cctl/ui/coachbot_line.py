"""This module exposes the CoachbotLine textualize widget."""

from typing import Union
import numpy as np
from rich.console import RenderableType
from textual.reactive import reactive
from textual.color import Color
from textual.widget import Widget
from textual.widgets import Static
from cctl.models import Coachbot


class _CoachbotBooted(Widget):
    is_on = reactive(None)

    def render(self) -> RenderableType:
        return 'On' if self.is_on else 'Off'


class _CoachbotPosition(Widget):
    pos = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.pos is None else str(self.pos)


class _CoachbotOsVersion(Widget):
    version = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.version is None else self.version


class _CoachbotBatVoltage(Widget):
    voltage = reactive(None)

    def render(self) -> RenderableType:
        if self.voltage is not None:
            if self.voltage >= 3.8:
                color = Color(0, 255, 0)
            elif self.voltage >= 3.6:
                color = Color(255, 255, 0)
            else:
                color = Color(255, 0, 0)
            self.styles.color = color
            return f'{self.voltage:1.02f}'
        return '?'


class _CoachbotTheta(Widget):
    theta = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.theta is None else f'{self.theta:.2f}'


class _CoachbotUserOn(Widget):
    is_on = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.is_on is None else ('⚙️' if self.is_on else '🛑')


class _CoachbotUserName(Widget):
    script_name = reactive(None)
    MAX_LEN = 23

    def render(self) -> RenderableType:
        return '?' if self.name is None \
            else (self.name if len(self.name) <= self.__class__.MAX_LEN
                  else f'{self.name[:self.__class__.MAX_LEN - 3]}...')


class _CoachbotUserAuthor(Widget):
    script_author = reactive(None)
    MAX_LEN = 23

    def render(self) -> RenderableType:
        return '?' if self.name is None \
            else (self.name if len(self.name) <= self.__class__.MAX_LEN
                  else f'{self.name[:self.__class__.MAX_LEN - 3]}...')


class _CoachbotUserVersion(Widget):
    version = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.version is None else self.version


class CoachbotStateDisplay(Static):
    """A widget to display the current coachbot state."""

    def __init__(self,
                 bot_id: int,
                 renderable: RenderableType = "", *,
                 expand: bool = False,
                 shrink: bool = False,
                 markup: bool = True,
                 name: Union[str, None] = None,
                 id: Union[str, None] = None,
                 classes: Union[str, None] = None) -> None:
        super().__init__(renderable, expand=expand, shrink=shrink,
                         markup=markup, name=name, id=id,
                         classes=f'{classes} coachbot-line')
        self.bot_id = bot_id

    def update_coachbot(self, bot: Coachbot):
        self._booted_msg.is_on = bot.state.is_on
        self._pos.pos = bot.state.position
        self._os_version.version = bot.state.os_version
        self._bat_v.voltage = bot.state.bat_voltage
        self._theta.theta = bot.state.theta
        self._user_on.is_on = bot.state.user_code_state.is_running
        self._user_name.script_name = bot.state.user_code_state.name
        self._user_author.script_author = bot.state.user_code_state.author
        self._user_version.version = bot.state.user_code_state.version

    def compose(self):
        yield Static(f'{self.bot_id}', classes='coachbot-line__id')
        self._booted_msg = _CoachbotBooted(classes='coachbot-line__is-on')
        yield self._booted_msg
        self._os_version = _CoachbotOsVersion(classes='coachbot-line__os-ver')
        yield self._os_version
        self._bat_v = _CoachbotBatVoltage(
            classes='coachbot-line__bat-voltage')
        yield self._bat_v
        self._pos = _CoachbotPosition(classes='coachbot-line__position')
        yield self._pos
        self._theta = _CoachbotTheta(classes='coachbot-line__theta')
        yield self._theta
        self._user_on = _CoachbotUserOn(classes='coachbot-line__script-state')
        yield self._user_on
        self._user_name = _CoachbotUserName(
            classes='coachbot-line__script-name')
        yield self._user_name
        self._user_author = _CoachbotUserAuthor(
            classes='coachbot-line__script-author')
        yield self._user_author
        self._user_version = _CoachbotUserVersion(
            classes='coachbot-line__script-version')
        yield self._user_version


class CoachbotStateHeaderDisplay(Static):
    """The table header widget."""
    def compose(self):
        yield Static('ID', classes='coachbot-line__id')
        yield Static('Boot', classes='coachbot-line__is-on')
        yield Static('Version', classes='coachbot-line__os-ver')
        yield Static('Voltage', classes='coachbot-line__bat-voltage')
        yield Static('Position', classes='coachbot-line__position')
        yield Static('Theta', classes='coachbot-line__theta')
        yield Static('State', classes='coachbot-line__script-state')
        yield Static('Name', classes='coachbot-line__script-name')
        yield Static('Author', classes='coachbot-line__script-author')
        yield Static('Version', classes='coachbot-line__script-version')
