"""
Generators for interval graph.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional

from collections.abc import Iterable, Sized

import networkx as nx
import pandas as pd

__all__ = ["interval_graph"]


def get_intervals_as_list_of_intervals(
    intervals: Iterable,
    node_ids: Optional[Iterable]=None,
) -> tuple[list[tuple[Any, Any]], list[int]]:
    if isinstance(intervals, pd.DataFrame):
        intervals = intervals.to_numpy()

    for interval in intervals:
        if not (
            isinstance(interval, Iterable)
            and isinstance(interval, Sized)
            and len(interval) == 2
        ):
            raise TypeError(
                "Each interval must have length 2, and be a iterable such as tuple or list."
            )

        interval = tuple(interval)
        if interval[0] > interval[1]:
            raise ValueError(f"Interval must have lower value first. Got {interval}")

    intervals = list(map(tuple, intervals))

    if node_ids is None:
        node_ids = range(len(intervals))
    node_ids = list(node_ids)
    if len(node_ids) != len(intervals):
        raise ValueError(
            f"node_ids and intervals should be of same size "
            f"(got respectively {len(node_ids)} and {len(intervals)})"
        )

    return intervals, node_ids

#@nx._dispatchable(graphs=None, returns_graph=True)
def interval_graph(
    intervals: Iterable,
    filter_func: Optional[Callable]=None,
    node_ids: Optional[Iterable]=None,
) -> nx.Graph:
    """Generates an interval graph for a list of intervals given.

    In graph theory, an interval graph is an undirected graph formed from a set
    of closed intervals on the real line, with a vertex for each interval
    and an edge between vertices whose intervals intersect.
    It is the intersection graph of the intervals.

    More information can be found at:
    https://en.wikipedia.org/wiki/Interval_graph

    Parameters
    ----------
    intervals : a sequence of intervals, say (l, r) where l is the left end,
    and r is the right end of the closed interval.

    Returns
    -------
    G : networkx graph

    Examples
    --------
    >>> intervals = [(-2, 3), [1, 4], (2, 3), (4, 6)]
    >>> G = nx.interval_graph(intervals)
    >>> sorted(G.edges)
    [((-2, 3), (1, 4)), ((-2, 3), (2, 3)), ((1, 4), (2, 3)), ((1, 4), (4, 6))]

    Raises
    ------
    :exc:`TypeError`
        if `intervals` contains None or an element which is not
        collections.abc.Sequence or not a length of 2.
    :exc:`ValueError`
        if `intervals` contains an interval such that min1 > max1
        where min1,max1 = interval
    """
    intervals, node_ids = get_intervals_as_list_of_intervals(intervals, node_ids)

    nodes = [(i, {"interval": interval}) for i, interval in zip(node_ids, intervals)]
    nodes = sorted(nodes, key=lambda k: k[1]["interval"][0])
    
    graph: nx.Graph = nx.Graph()
    graph.add_nodes_from(nodes)

    import itertools
    for node_id_i, node_id_j in itertools.combinations(graph, 2):
        start1, end1 = graph.nodes[node_id_i]["interval"]
        start2, end2 = graph.nodes[node_id_j]["interval"]
        if filter_func is None or filter_func(node_id_i, node_id_j):
            if end1 >= start2:
                graph.add_edge(node_id_i, node_id_j)

    return graph


def build_graph(
    intervals: Iterable,
    filter_func: Callable,
    node_ids: Optional[Iterable]=None,
) -> nx.Graph:
    """Generates an interval graph for a list of intervals given.

    In graph theory, an interval graph is an undirected graph formed from a set
    of closed intervals on the real line, with a vertex for each interval
    and an edge between vertices whose intervals intersect.
    It is the intersection graph of the intervals.

    More information can be found at:
    https://en.wikipedia.org/wiki/Interval_graph

    Parameters
    ----------
    intervals : a sequence of intervals, say (l, r) where l is the left end,
    and r is the right end of the closed interval.

    Returns
    -------
    G : networkx graph

    Examples
    --------
    >>> intervals = [(-2, 3), [1, 4], (2, 3), (4, 6)]
    >>> G = nx.interval_graph(intervals)
    >>> sorted(G.edges)
    [((-2, 3), (1, 4)), ((-2, 3), (2, 3)), ((1, 4), (2, 3)), ((1, 4), (4, 6))]

    Raises
    ------
    :exc:`TypeError`
        if `intervals` contains None or an element which is not
        collections.abc.Sequence or not a length of 2.
    :exc:`ValueError`
        if `intervals` contains an interval such that min1 > max1
        where min1,max1 = interval
    """
    intervals, node_ids = get_intervals_as_list_of_intervals(intervals, node_ids)

    nodes = [(i, {"interval": interval}) for i, interval in zip(node_ids, intervals)]
    nodes = sorted(nodes, key=lambda k: k[1]["interval"][0])

    graph: nx.Graph = nx.Graph()
    graph.add_nodes_from(nodes)

    import itertools
    for node_id_i, node_id_j in itertools.combinations(graph, 2):
        if filter_func(node_id_i, node_id_j):
            graph.add_edge(node_id_i, node_id_j)

    return graph
