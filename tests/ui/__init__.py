#!/usr/bin/env python3

"""This package exposes the main CCTL manage application."""

from textual.app import App
from textual.widgets import Footer, Header

from cctl.models.coachbot import Coachbot
from cctl.ui.coachbot_line import CoachbotStateDisplay, \
    CoachbotStateHeaderDisplay
import importlib.resources as pkg_resources
from cctl_static import ui as static_ui


class ManageApp(App):
    """This exposes the main ``cctl manage`` app."""

    def _update_model(self, bot: Coachbot):
        display_widget = \
            self.query_one(f'#coachbot-state-display__{bot.identifier}')
        assert isinstance(display_widget, CoachbotStateDisplay)
        display_widget.update_coachbot(bot)

    def compose(self):
        yield Header()
        yield CoachbotStateHeaderDisplay()
        for i in range(100):
            yield CoachbotStateDisplay(i, id=f'coachbot-state-display__{i}')
        yield Footer()


# Need to monkey patch the class because the CSS path is only available at
# runtime and pkg_resources only exposes a context manager
with pkg_resources.path(static_ui, 'app.css') as css_path:
    ManageApp.CSS_PATH = css_path
