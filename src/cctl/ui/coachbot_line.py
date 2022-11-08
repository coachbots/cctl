"""This module exposes the CoachbotLine textualize widget."""

from typing import Union
from rich.console import RenderableType
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from cctl.models import Coachbot


class _CoachbotBooted(Widget):
    is_on = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.is_on is None else 'On' if self.is_on else 'Off'


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
        return '?' if self.voltage is None else f'{self.voltage:1.02f}'


class _CoachbotTheta(Widget):
    theta = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.theta is None else f'{self.theta:.2f}'


class _CoachbotUserOn(Widget):
    is_on = reactive(None)

    def render(self) -> RenderableType:
        return '?' if self.is_on is None \
            else ('Running' if self.is_on else 'Paused')


class _CoachbotUserName(Widget):
    name = reactive(None)
    MAX_LEN = 23

    def render(self) -> RenderableType:
            return '?' if self.name is None \
                else (self.name if len(self.name) <= self.__class__.MAX_LEN
                      else f'{self.name[:self.__class__.MAX_LEN - 3]}...')


class _CoachbotUserAuthor(Widget):
    name = reactive(None)
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
        self.query_one('.coachbot-line__is-on').is_on = bot.state.is_on
        self.query_one('.coachbot-line__position').pos = bot.state.position
        self.query_one('.coachbot-line__os-ver').version = bot.state.os_version
        self.query_one('.coachbot-line__bat-voltage').voltage = \
            bot.state.bat_voltage
        self.query_one('.coachbot-line__theta').theta = \
            bot.state.theta
        self.query_one('.coachbot-line__script-state').is_on = \
            bot.state.user_code_state.is_running
        self.query_one('.coachbot-line__script-name').name = \
            bot.state.user_code_state.name
        self.query_one('.coachbot-line__script-author').name = \
            bot.state.user_code_state.author
        self.query_one('.coachbot-line__script-version').version = \
            bot.state.user_code_state.version

    def compose(self):
        yield Static(f'{self.bot_id}', classes='coachbot-line__id')
        yield _CoachbotBooted(classes='coachbot-line__is-on')
        yield _CoachbotOsVersion(classes='coachbot-line__os-ver')
        yield _CoachbotBatVoltage(classes='coachbot-line__bat-voltage')
        yield _CoachbotPosition(classes='coachbot-line__position')
        yield _CoachbotTheta(classes='coachbot-line__theta')
        yield _CoachbotUserOn(classes='coachbot-line__script-state')
        yield _CoachbotUserName(classes='coachbot-line__script-name')
        yield _CoachbotUserAuthor(classes='coachbot-line__script-author')
        yield _CoachbotUserVersion(classes='coachbot-line__script-version')


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
