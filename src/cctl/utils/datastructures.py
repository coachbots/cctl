#!/usr/bin/env python

"""This module exposes common data structures."""

from typing import Callable, List, TypeVar, Generic

T = TypeVar('T')

class Tree(Generic[T]):
    """A simple tree."""
    def __init__(self, value: T) -> None:
        self.root = value
        self.children: List[T] = []

    def apply(self, predicate: Callable[[T], T]) -> None:
        """Applies a function to the tree."""
        self.root = predicate(self.root)
        self.children = [predicate(child) for child in self.children]
