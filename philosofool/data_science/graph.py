"""Functions for working with graphs"""

from collections.abc import Hashable, Iterable, Mapping, Callable
from graphlib import TopologicalSorter
from typing import Any

import numpy as np  # noqa: F401
import pandas as pd
from numpy.typing import ArrayLike

# from philosofool.functional.functional import compose_function


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


class MetricGraph:
    """Calculate metrics from a model of metrics.

    The model of metrics is a mapping of metrics to callables and metrics to dependencies.
    The class handles the calculation of metrics in a Pandas dataframe.

    Follows standard graphlib conventions: a graph is a mapping from Hashable elements to
    a Hashable sequence.
    """

    def __init__(self, dependency_graph: Mapping[Any, tuple[Hashable, ...]], metric_functions: Mapping[Any, Callable]):
        self.metric_functions = metric_functions
        self.dependency_graph = dependency_graph

    @classmethod
    def from_model(cls, model: Mapping[Any, tuple[Callable, tuple[Hashable, ...]]]) -> 'MetricGraph':
        """Construct an instance from a mapping of keys to the metric function and dependency names."""
        metric_functions = {}
        dependency_graph = {}
        for key, (fn, deps) in model.items():
            metric_functions[key] = fn
            dependency_graph[key] = deps
        return cls(dependency_graph, metric_functions)

    def calculate_metric(self, metric: Hashable, calculated_metrics: Mapping[Any, ArrayLike]) -> ArrayLike:
        """Calculate metric."""
        calculator = self.metric_functions[metric]
        dependencies = self.dependency_graph[metric]
        data = [calculated_metrics[metric] for metric in dependencies]
        return calculator(*data)

    def calculate_metrics(self, df: pd.DataFrame, metrics: Iterable[Hashable]) -> Mapping[Any, ArrayLike]:
        """Calculate the metrics from dataframe."""
        sorted_metrics_and_dependencies = self._sort_metrics_topologically(
            self.get_metric_dependencies(metrics).union(metrics)
        )
        calculated_metrics = {}
        for metric in sorted_metrics_and_dependencies:
            match df.get(metric):
                case None:
                    calculated_metrics[metric] = self.calculate_metric(metric, calculated_metrics)
                case value:
                    calculated_metrics[metric] = value
        return {metric: calculated_metrics[metric] for metric in metrics}

    def add_metrics(self, df: pd.DataFrame, metrics: Iterable[Hashable]) -> pd.DataFrame:
        """Add the metrics to a dataframe."""
        calculated_metrics = self.calculate_metrics(df, metrics)
        return df.assign(**calculated_metrics)  # type: ignore Pandas is not hinted for assign, but accepts dicts.


    def get_metric_dependencies(self, metrics: Iterable[Hashable]) -> set:
        """Get the dependencies needed to calculate metrics."""
        dependencies = set()
        for metric in metrics:
            metric_ancestors = get_ancestors(metric, self.dependency_graph, seen=dependencies)
            dependencies = dependencies.union(metric_ancestors)
        return dependencies

    def _topologically_sorted_metrics(self) -> Mapping[Any, int]:
        sorted_metrics = TopologicalSorter(self.dependency_graph).static_order()
        return {metric: i for i, metric in enumerate(sorted_metrics)}

    def _sort_metrics_topologically(self, metrics: Iterable[Hashable]) -> list[Hashable]:
        return sorted(metrics, key=lambda metric: self._topologically_sorted_metrics()[metric])
