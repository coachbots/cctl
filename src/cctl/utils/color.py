#!/usr/bin/env python

"""This module exposes color-related functions and utilities."""

from typing import Tuple

RED = '#ff0000'
GREEN = '#00ff00'
BLUE = '#0000ff'
YELLOW = '#ffff00'
CYAN = '#00ffff'
PURPLE = '#ff00ff'


def hex_to_rgb(hx_str: str) -> Tuple[int, int, int]:
    """Converts hex color to RGB.

    Raises:
        RuntimeError: The inputted string is not a color string.
    """
    try:
        return (
            int((stripped := hx_str.lstrip('#'))[:2], 16),
            int(stripped[2:4], 16),
            int(stripped[4:], 16)
        )
    except IndexError as err:
        raise RuntimeError from err


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Converts RGB to a Hex string."""
    return '#%02x%02x%02x' % rgb  # pylint: disable=consider-using-f-string
