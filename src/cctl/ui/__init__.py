#!/usr/bin/env python3

"""This package exposes the main CCTL manage application."""

from typing import Callable, List, Optional
from reactivex import Observable
from textual.app import App
from textual.widgets import Footer, Header

import reactivex.operators as rxops
from cctl.models.coachbot import Coachbot
from cctl.ui.coachbot_line import CoachbotStateDisplay, \
    CoachbotStateHeaderDisplay
import importlib.resources as pkg_resources
from cctl_static import ui as static_ui


class ManageApp(App):
    """This exposes the main ``cctl manage`` app."""

    BINDINGS = [
        ('d', 'toggle_dark', 'Toggle Dark Mode'),
        ('q', 'quit', 'Quit')
    ]

    def __init__(self,
                 observable_stream: Observable[List[Coachbot]],
                 on_quit_callback: Optional[Callable[[], None]] = None,
                 driver_class=None):
        super().__init__(driver_class, None, False)

        self.observable_stream = observable_stream
        self.on_quit = on_quit_callback
        self.coachbot_lines = []

        data_stream_60hz = self.observable_stream.pipe(
            rxops.debounce(1.0 / 60.0))
        data_stream_60hz.subscribe(on_next=self._update_all_models)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_quit(self) -> None:
        if self.on_quit is not None:
            self.on_quit()
        self.exit()

    def _update_all_models(self, bots: List[Coachbot]):
        for bot in bots:
            self._update_model(bot)

    def _update_model(self, bot: Coachbot):
        display_widget = self.coachbot_lines[bot.identifier]
        assert isinstance(display_widget, CoachbotStateDisplay)
        display_widget.update_coachbot(bot)

    def compose(self):
        yield Header()
        yield CoachbotStateHeaderDisplay()
        self.coachbot_lines = []
        for i in range(100):
            coachbot_line = CoachbotStateDisplay(
                i, id=f'coachbot-state-display__{i}')
            self.coachbot_lines.append(coachbot_line)
            yield coachbot_line
        yield Footer()


# Need to monkey patch the class because the CSS path is only available at
# runtime and pkg_resources only exposes a context manager
with pkg_resources.path(static_ui, 'app.css') as css_path:
    ManageApp.CSS_PATH = css_path
