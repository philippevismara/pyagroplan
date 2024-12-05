"""
Generators for interval graph.
"""
from collections.abc import Sequence

import networkx as nx

__all__ = ["interval_graph"]


#@nx._dispatchable(graphs=None, returns_graph=True)
def interval_graph(intervals, filter_func=None):
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
    intervals = list(intervals)
    for interval in intervals:
        if not (isinstance(interval, Sequence) and len(interval) == 2):
            raise TypeError(
                "Each interval must have length 2, and be a "
                "collections.abc.Sequence such as tuple or list."
            )
        if interval[0] > interval[1]:
            raise ValueError(f"Interval must have lower value first. Got {interval}")

    graph = nx.Graph()

    nodes = [(i, {"interval": tuple(interval)}) for i, interval in enumerate(intervals)]
    graph.add_nodes_from(nodes)

    for i in list(graph):
        min1, max1 = graph.nodes[i]["interval"]
        for j in list(graph)[i+1:]:
            min2, max2 = graph.nodes[j]["interval"]
            if filter_func is None or filter_func(i, j):
                if max1 >= min2 and max2 >= min1:
                    graph.add_edge(i, j)

    return graph
