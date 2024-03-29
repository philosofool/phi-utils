"""Functions for working with graphs"""

from collections.abc import Hashable, Iterable, Mapping, Callable
import functools
from graphlib import TopologicalSorter
from typing import Any, Optional

import numpy as np  # noqa: F401
import pandas as pd
from numpy.typing import ArrayLike


def get_ancestors(value: Hashable, graph: dict[Any, Iterable], ancestors=set()) -> set:
    """Return all ancestors of `value` from a directed graph."""
    ancestors = ancestors.copy()
    graph = graph.copy()
    predecessors = graph.get(value, [])
    for predecessor in predecessors:
        if predecessor in ancestors:
            continue
        ancestors.add(predecessor)
        ancestors.update(get_ancestors(predecessor, graph, ancestors=ancestors))
    return ancestors


class MetricGraph:
    """Calculate metrics from a model of metrics.

    The model of metrics is a mapping of metrics to callables and metrics to dependencies.
    The class handles the calculation of metrics in a Pandas dataframe.

    Follows standard graphlib conventions: a graph is a mapping from Hashable elements to
    a Hashable sequence.

    Attributes
    ----------
        dependency_graph
            The model of dependency: A mapping from hashable values to a sequence of hashable values.
        metric_functions
            Mapping of metrics from the graph to functions that calculate them.

            This assumes that the ordering of dependencies corresponds to the order in the dependency graph.

    Class Methods
    -------------
        from_model:
           Construct an instance from a model, i.e., a mapping from names to a pair of a function and a dependency list.
        model_to_graph_and_functions:
            Parse a model into metric functions and dependencies graph.

    Methods
    -------
        calculate_metrics:
            Compute the metrics from a DataFrame without recalculating dependencies.
        recalculate_metrics:
            Compute metrics from a DataFrame, recalculating all dependencies.
        add_metrics:
            Add metric calculations to a DataFrame.
        get_metric_dependencies:
            Find all metrics required to compute a metric.
    """

    def __init__(self, dependency_graph: Mapping[Any, tuple[Hashable, ...]], metric_functions: Mapping[Any, Callable]):
        self.metric_functions = metric_functions
        self.dependency_graph = dependency_graph

    @classmethod
    def from_model(cls, model: Mapping[Any, tuple[Callable, tuple[Hashable, ...]]]) -> 'MetricGraph':
        """Construct an instance from a mapping of keys to the metric function and dependency names."""
        metric_functions, dependency_graph = cls.model_to_graph_and_functions(model)
        return cls(dependency_graph, metric_functions)

    @classmethod
    def model_to_graph_and_functions(cls, model:  Mapping[Any, tuple[Callable, tuple[Hashable, ...]]]) -> tuple[dict[Any, Callable], dict[Any, tuple[Hashable, ...]]]:
        """Parse a model into two dictionaries, the metric funcions and the dependency graph."""
        metric_functions = {}
        dependency_graph = {}
        for key, (fn, deps) in model.items():
            metric_functions[key] = fn
            dependency_graph[key] = deps
        return metric_functions, dependency_graph

    def _calculate_metric(self, metric: Hashable, calculated_metrics: Mapping[Any, ArrayLike]) -> ArrayLike:
        """Calculate metric."""
        calculator = self.metric_functions[metric]
        dependencies = self.dependency_graph[metric]
        data = [calculated_metrics[metric] for metric in dependencies]
        return calculator(*data)

    def model(self, metrics: Optional[Iterable] = None) -> dict[tuple[Callable, tuple[str, ...]]]:
        """Return a dictionary associating each metric with it's callable and dependencies."""
        if metrics is None:
            metrics = list(self.dependency_graph)
        return {metric: (self.metric_functions[metric], self.dependency_graph[metric]) for metric in metrics}

    def calculate_metrics(self, df: pd.DataFrame, metrics: Iterable[Hashable]) -> Mapping[Any, ArrayLike]:
        """Calculate the metrics from dataframe.

        Calculates all metrics passed (even if they are already in the data) but does
        not recalculate dependencies, while recalculate_metrics will recalculate metrics
        and all their dependencies, recursively.

        This method is more efficient than recalculate metrics. Additionally, if "grandparent"
        metrics are missing, calculations can still complete.
        """
        dependencies = functools.reduce(lambda a, b: a.union(get_ancestors(b, self.dependency_graph, a)), metrics, set(df.columns.intersection(self.dependency_graph)))
        sorted_metrics_and_dependencies = self._sort_metrics_topologically(dependencies.union(metrics))
        calculated_metrics = {}
        _metrics = set(metrics)  # fast membership.
        for metric in sorted_metrics_and_dependencies:
            match df.get(metric), metric in _metrics:
                case None, _:
                    calculated_metrics[metric] = self._calculate_metric(metric, calculated_metrics)
                case _, True:
                    calculated_metrics[metric] = self._calculate_metric(metric, calculated_metrics)
                case value, False:
                    calculated_metrics[metric] = value
        return {metric: calculated_metrics[metric] for metric in metrics}

    def recalculate_metrics(self, df: pd.DataFrame, metrics: Iterable[Hashable]) -> Mapping[Any, ArrayLike]:
        """Recalculate the metrics from dataframe.

        Calculates all metrics and their dependencies, recursively, and will raise an
        KeyError if any metric is missing, while calculate_metrics only calculates
        metrics explicitly passed and missing dependencies.

        This method is useful following groupby-aggregate and other transformations
        that may require downstream metrics to be recalculated.
        """
        sorted_metrics_and_dependencies = self._sort_metrics_topologically(
            self.get_metric_dependencies(metrics).union(metrics)
        )
        calculated_metrics = {}
        for metric in sorted_metrics_and_dependencies:
            calculated_metrics[metric] = self._calculate_metric(metric, calculated_metrics)
        return {metric: calculated_metrics[metric] for metric in metrics}

    @property
    def metrics(self) -> tuple:
        """Return the metrics in the graph, which are topologically sorted."""
        return tuple(self._topologically_sorted_metrics())

    def add_metrics(self, df: pd.DataFrame, metrics: Iterable[Hashable]) -> pd.DataFrame:
        """Add the metrics to a dataframe."""
        calculated_metrics = self.calculate_metrics(df, metrics)
        return df.assign(**calculated_metrics)  # type: ignore Pandas is not hinted for assign, but accepts dicts.

    def get_metric_dependencies(self, metrics: Iterable[Hashable]) -> set:
        """Get the dependencies needed to calculate metrics."""
        dependencies = set()
        for metric in metrics:
            metric_ancestors = get_ancestors(metric, self.dependency_graph, ancestors=dependencies)
            dependencies = dependencies.union(metric_ancestors)
        return dependencies


    def _topologically_sorted_metrics(self) -> dict[Any, int]:
        sorted_metrics = TopologicalSorter(self.dependency_graph).static_order()
        return {metric: i for i, metric in enumerate(sorted_metrics)}

    def _sort_metrics_topologically(self, metrics: Iterable[Hashable]) -> list[Hashable]:
        _top_sorted_metrics = self._topologically_sorted_metrics()
        return sorted(metrics, key=lambda metric: _top_sorted_metrics[metric])
