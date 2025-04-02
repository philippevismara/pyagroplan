from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

import datetime

import networkx as nx


def timedelta_dataframe_to_directed_graph(
    df: pd.DataFrame,
    name: str,
) -> nx.DiGraph:
    graph = nx.from_pandas_adjacency(df != datetime.timedelta(weeks=0), nx.DiGraph)
    values = {(u, v): df.loc[u, v] for u, v in graph.edges}
    nx.set_edge_attributes(
        graph,
        values,
        name=name,
    )
    return graph
