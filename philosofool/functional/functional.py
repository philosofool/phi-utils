"""Utilities for functional programming."""

from collections.abc import Callable
from typing import Any

import functools


def _collect_annotations(obj: Any) -> dict:
    try:
        return obj.__annotations__.copy()
    except AttributeError:
        return {}


def _compose_2(f: Callable, g: Callable) -> Callable:
    """Compose a pair of functions to one, returning like g(f(x)).

    This is largely a helper to simplify compose_function.

    """
    annotations = _collect_annotations(f)
    return_annotations = _collect_annotations(g).get('return', 'no typing provided')

    annotations.update({'return': return_annotations})
    if annotations['return'] == 'no typing provided':
        del(annotations['return'])

    def composed_fn(*args, **kwargs):
        return g(f(*args, **kwargs))

    composed_fn.__annotations__ = annotations

    return composed_fn


def compose_function(*funcs: Callable) -> Callable:
    """Compose a function, applying funcs from left to right."""
    return functools.reduce(lambda f, g: _compose_2(f, g), funcs)