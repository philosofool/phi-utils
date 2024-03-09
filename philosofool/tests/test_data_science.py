
from philosofool.data_science.graph import get_ancestors, MetricGraph

import numpy as np
import pandas as pd

def test_get_ancestors():
    """Test of get_ancestors."""
    value = 'a'
    graph = {'a': ('b', 'c', 'd'), 'c': ('b', 'e'), 'd': ('e', 'f')}
    result = get_ancestors(value, graph)
    expected = {'f', 'd', 'b', 'c', 'e'}
    assert result == expected, f"Got {result}"

    cyclic_graph = {'a': ('b',), 'b': ('a',)}
    assert 'a' in get_ancestors('a', cyclic_graph)
    assert 'a' in get_ancestors('a', {'a': ('a',)})

def test_MetricGraph():
    """Test of MetricGraph."""
    # test uses baseball stats.
    metric_dependencies = {
        'BA': ('H', 'AB'),  # batting average: hits, at bats
        'AB': ('PA', 'BB'),  # At bats: (Plate appearances, base on balls (walks))
        'H': ('1B', '2B', '3B', 'HR')  # Hits exists in calcs below.
    }
    metric_functions = {
        'BA': np.divide,
        'AB': lambda pa, bb: pa - bb
    }
    data = pd.DataFrame({
        'player': ['jackie', 'babe'],
        'H': [170, 150],
        'BB': [80, 100],
        'PA': [600, 600]
    })
    metric_graph = MetricGraph(metric_dependencies, metric_functions)
    result = metric_graph.calculate_metrics(data, ['BA'])
    assert 'AB' not in result
    assert np.allclose(result['BA'], np.divide([170, 150], [600 - 80, 600 - 100])), f"got {result}"
    result_add = metric_graph.add_metrics(data, ['BA','AB'])
    assert all(k in result_add for k in ['BA', 'AB'])

if __name__ == '__main__':
    test_get_ancestors()
    test_MetricGraph()
    print("All tests passed.")
