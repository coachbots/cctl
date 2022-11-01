from collections.abc import Iterable
from reactivex import Observable
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer

from cctl.models.coachbot import Coachbot


class CCTLManageTable(DataTable):
    def __init__(self, *, name, id=None, classes=None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.add_column('ID')
        self.add_column('On?')
        self.add_column('OS Ver.')
        self.add_column('Position')
        self.add_column('Angle')
        self.add_column('Batt.')
        self.add_column('User Running')
        self.add_column('Name')
        self.add_column('Author')
        self.add_column('User Ver.')
        self.zebra_stripes = True

    def add_coachbot_row(self, bot: Coachbot) -> None:
        """Adds a row to the table of the given coachbot."""
        self.add_row(
            str(bot.identifier),
            ('On' if on else 'Off')
            if (on := bot.state.is_on) is not None
            else '?',
            str(osv) if (osv := bot.state.os_version) is not None else '?',
            str(pos) if (pos := bot.state.position) is not None else '?',
            str(th) if (th := bot.state.theta) is not None else '?',
            str(v) if (v := bot.state.bat_voltage) is not None else '?',
            ('Yes' if v else 'No')
            if (v := bot.state.user_code_state.is_running) is not None
            else '?',
            s if (s := bot.state.user_code_state.name) is not None else '?',
            a if (a := bot.state.user_code_state.author) is not None else '?',
            str(v)
            if (v := bot.state.user_code_state.version) is not None
            else '?',
        )


class CCTLManageApp(App):
    """A Textual app for cctl manage."""
    BINDINGS = [
        ('q', 'quit', 'Quit'),
        ('d', 'toggle_dark', 'Toggle Dark Mode')
    ]

    def __init__(self, observable: Observable):
        super().__init__()
        self.data_observable = observable
        self.data_observable.subscribe(lambda coachbots:
                                       self.rerender(coachbots))
        self.table = CCTLManageTable(name='Coachbot List')

    def rerender(self, coachbots: Iterable[Coachbot]) -> None:
        self.table = CCTLManageTable(name='Coachbot List')
        for bot in coachbots:
            self.table.add_coachbot_row(bot)

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.table
        yield Footer()

    def action_quit(self) -> None:
        self.exit(0)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
