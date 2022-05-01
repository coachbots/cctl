#!/usr/bin/env python

from . import MockManagedCoachbot


def main():
    with MockManagedCoachbot() as mock_bot:
        mock_bot.listen(100)


if __name__ == '__main__':
    main()
