"""Functions for working with graphs"""

from collections.abc import Hashable, Iterable, Mapping
from typing import Any


def get_ancestors(value: Hashable, graph: Mapping[Any, Iterable], seen=None) -> set:
    """Return all ancestors of `value` from an acyclic graph."""
    seen = seen or set()
    predecessors = graph.get(value, set())
    if predecessors:
        for predecessor in predecessors:
            if predecessor in seen:
                continue
            seen.add(predecessor)
            seen.update(get_ancestors(predecessor, graph, seen=seen))
    return seen


def test_get_ancestors():
    """Test of get_ancestors."""
    value = 'a'
    graph = {'a': ('b', 'c', 'd'), 'c': ('b', 'e'), 'd': ('e', 'f')}
    result = get_ancestors(value, graph)
    expected = {'f', 'd', 'b', 'c', 'e'}
    assert result == expected
    print("test passed.")


if __name__ == '__main__':
    test_get_ancestors()
