#!/usr/bin/env python

"""Defines commonly used string parsers."""

import re
from typing import List, Literal, Union


def iter_string(iter_str: str) -> Union[List[int], Literal['all']]:
    """Parses the id parameter ensuring that it fits the format:
        ^(\\d+)$ or ^(\\d+)-(\\d+)$. If 'all' is given, then the function
        returns true, otherwise returns a list of targets to be turned on.
    """
    single_id_regex = r'^(\d+)$'
    range_regex = r'^(\d+)-(\d+)$'

    if iter_str.lower() == 'all':
        return 'all'

    # Try matching with range first:
    match = re.match(range_regex, iter_str)
    if match is not None:
        return list(range(int(match.group(1)), int(match.group(2)) + 1))

    # Try matching with single:
    match = re.match(single_id_regex, iter_str)
    if match is not None:
        val = int(match.group(1))
        return list(range(val, val + 1))

    raise AttributeError(f'Unparsable String {iter_str}.')
