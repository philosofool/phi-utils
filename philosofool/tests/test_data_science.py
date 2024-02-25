
from philosofool.data_science.graph import get_ancestors


def test_get_ancestors():
    """Test of get_ancestors."""
    value = 'a'
    graph = {'a': ('b', 'c', 'd'), 'c': ('b', 'e'), 'd': ('e', 'f')}
    result = get_ancestors(value, graph)
    expected = {'f', 'd', 'b', 'c', 'e'}
    assert result == expected


if __name__ == '__main__':
    test_get_ancestors()
