# -*- coding: utf-8 -*-

"""Presents logging manipulation functions and classes.

Warning: This file is not currently finished. Please refrain from using it.
"""

from enum import Enum, IntEnum
from typing import Generator, Iterable, Optional
from cctl.api import configuration
from cctl.api.bot_ctl import Coachbot
from cctl.utils.net import read_remote_file


class LogLevel(IntEnum):
    """Represents the severity of a log."""
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0


class LogSource(Enum):
    """Represents the source of a log (system-code or user-code)"""
    SYS = 1
    USER = 2


class LogEntry:
    """This class represents a singular log entry.

    Parameters:
        bot_id (int): The robot id
        level (LogLevel): The log level.
        source (LogSource): The log source.
        message (str): The log message.

    Note:
        This class is not a dataclass because we require ``python3.6`` support
        and dataclasses were only introduced in ``python3.7``.
    """

    STRING_FORMAT = '%(bot_id)s [%(source)s-%(level)s]: %(message)s'

    def __init__(self, bot: Coachbot, level: LogLevel,
                 source: LogSource, message: str) -> None:
        self.bot = bot
        self.level = level
        self.source = source
        self.message = message

    def __str__(self) -> str:
        return LogEntry.STRING_FORMAT.format(
            bot_id=self.bot.identifier, source=self.source, level=self.level,
            message=self.message)

    @staticmethod
    def from_log_entry(log_entry: str) -> 'LogEntry':
        """Builds a LogEntry from a log_entry string.

        Parameters:
            log_entry (str): The log entry row.

        Returns:
            LogEntry: The log entry object.
        """
        raise NotImplementedError


def fetch(scrape_bots: Optional[Iterable[Coachbot]] = None) \
        -> Generator[LogEntry, None, None]:
    """This function fetches the modern python ``logging``-style logs from the
    Coachbots, returning all the logs.

    Properties:
        scrape_bots (Optional[Iterable[Coachbot]]): Whether bots should be
        scraped as well. If this Iterable is non-empty, then the function will
        also attempt to read the logs on the specified bots. This function
        makes no assumptions on whether those bots are online or not.

    Example:

    .. code-block:: python

       from cctl.api import logs

       # Note how verbose this is due to the lack of the := operator in py3.6
       for m_log in (for log in logs.fetch() if log.source == LogSource.SYS):
           # All m_logs are now only system logs.
           print(f'The system said: {m_log.message}')

    Returns:
        Generator: The generator where each value is a LogEntry with
        information pushed into it.
    """
    log_path = configuration.get_syslog_path()

    with open(log_path) as file:
        for log_entry_str in file:
            yield LogEntry.from_log_entry(log_entry_str)

    if scrape_bots is not None:
        for scrapable in scrape_bots:
            for line in read_remote_file(scrapable.address,
                                         log_path).split(b'\n'):
                yield LogEntry.from_log_entry(str(line))
