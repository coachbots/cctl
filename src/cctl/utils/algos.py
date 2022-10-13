from typing import Any, Callable, Iterable, List


def key_idx(xs: Iterable, callable: Callable) -> int:
    """Finds the index of the given callable. Raises ValueError if not found.
    """
    i = 0
    for x in xs:
        if callable(x):
            return i
        i += 1
    raise ValueError


def group_els(xs: Iterable, key: Callable = lambda x: x) -> List:
    """Returns a list where elements are pseudo-sorted, meaning all elements
    that test for equality are grouped together, so something like:

    .. code-block:: python

       group_els([1, 3, 2, 2, 3, 1]) == [1, 1, 2, 2, 3, 3]

    """
    outl = []
    for x in xs:
        try:
            outl.insert(key_idx(outl, lambda y: key(y) == key(x)), x)
        except ValueError:
            outl.append(x)
    return outl


def iterable_flatten(xss: Iterable[Iterable[Any]]) -> Iterable[Any]:
    """Flattens an iterable.

    Parameters:
        xss (Iterable[Iterable[Any]]) The input iterable.

    Returns:
        The flattened iterable.

    Example:
        .. code-block:: python

           list(iterable_flatten([[1, 2], [3]])) == [1, 2, 3]
    """
    return (x for xs in xss for x in xs)
