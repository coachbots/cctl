"""
This package exposes test suites that are convenient for testing the coachbots.

Think of this as the main runner you should use when running tests.
"""


import sys
import unittest
from collections.abc import Callable
from typing import Dict
from tests.feature.cli.test_cli_off import TestOffCommands
from tests.feature.cli.test_cli_on import TestOnCommands


def swarm_cli_short() -> unittest.TestSuite:
    """This test suite runs a short CLI-based test on the swarm.

    Purpose:
        The main purpose of this test suite is to ensure no regression has
        ocurred. This is a fast test suite and provides no guarantees, but
        should be run on all non-trivial PRs.

    Functions:
        This test suite attempts to boot on 9 coachbots, upload code to them,
        run them, pause them, and turn them off.

    Success condition:
        All commands exit out correctly and sucessfully.
    """
    test_suite = unittest.TestSuite()

    test_suite.addTest(TestOnCommands('test_on_range_90_99'))
    test_suite.addTest(TestOffCommands('test_off_range_90_99'))

    return test_suite


TEST_SUITES: Dict[str, Callable[[], unittest.TestSuite]] = {
    'swarm-cli-short': swarm_cli_short,
}


def main() -> None:
    runner = unittest.TextTestRunner()
    try:
        if sys.argv[2] in ('-h', '--help'):
            print(f'{sys.argv[1]}:\n{TEST_SUITES[sys.argv[1]].__doc__}')
            sys.exit(0)

        runner.run(TEST_SUITES[sys.argv[1]]())
    except KeyError:
        valid_tests = ','.join(TEST_SUITES.keys())
        print('The specified test does not exist. '
              f'Valid tests are {valid_tests}.', file=sys.stderr)
        sys.exit(1)


main()
