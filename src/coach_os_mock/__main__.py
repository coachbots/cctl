#!/usr/bin/env python

import time

from cctl.utils.math import Vec2

from . import MockManagedCoachbot


def main():
    with MockManagedCoachbot() as mock_bot:
        start_time = time.time()
        while True:
            delta_t = time.time() - start_time
            print(f'[T+{round(delta_t, 2)}s]\t\t', end='')
            mock_bot.listen(1)
            assert mock_bot.state.position is not None
            mock_bot.state.position += Vec2(0, 1)
            mock_bot.reply(1)


if __name__ == '__main__':
    main()
