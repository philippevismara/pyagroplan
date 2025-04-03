from __future__ import annotations

import networkx as nx
import pandas as pd
from collections.abc import Sequence

from .._typing import FilePath


class BedsData:
    """Handles beds data.

    Attributes
    ----------
    df_beds_data : pd.DataFrame
        DataFrame containing the raw data.
    beds_ids : list[int]
        List of all the beds ids.
    adjacency_list : pd.Series
        List of adjacency defining the proximity of the beds inside a same garden.
    adjacency_function : Callable[[int, int], bool]
        Adjacency function returning True if two beds are adjacent.
    n_beds : int
        Total number of beds.

    Parameters
    ----------
    df_beds_data : pd.DataFrame
        DataFrame containing the raw beds data.
    """

    def __init__(self, df_beds_data: pd.DataFrame | FilePath):
        if isinstance(df_beds_data, FilePath):
            from .data_loaders import CSVBedsDataLoader
            df_beds_data = CSVBedsDataLoader.load(df_beds_data)

        df_beds_data = df_beds_data.copy()

        self._check_df_beds_data(df_beds_data)

        self._df_beds_data = df_beds_data.copy()
        df_beds_data.columns = df_beds_data.columns.droplevel(0)
        self.df_beds_data = df_beds_data

    @property
    def n_beds(self) -> int:
        return len(self.df_beds_data)

    @property
    def beds_ids(self) -> list:
        return self._df_beds_data["metadata"]["bed_id"].to_numpy().tolist()

    @property
    def adjacency_lists(self) -> pd.DataFrame:
        return self._df_beds_data["adjacent_beds"]

    def __str__(self) -> str:
        return """BedsData(n_beds={})""".format(self.n_beds)

    def __len__(self) -> int:
        return self.n_beds


    def _check_df_beds_data(self, df_beds_data: pd.DataFrame) -> None:
        adjacency_lists = df_beds_data["adjacent_beds"]
        for adjacency_name, adjacency_list in adjacency_lists.items():
            for i in range(len(adjacency_lists)):
                if not (
                    isinstance(adjacency_list[i], Sequence)
                    and all(map(lambda x: isinstance(x, int), adjacency_list[i]))
                ):
                    raise ValueError(
                        f"'adjacent_beds' columns must contain list of ints "
                        f"({adjacency_name} is not correct)"
                    )

    def get_adjacency_graph(self, adjacency_name: str) -> nx.Graph:
        """Builds the adjacency graph.

        Parameters
        ----------
        adjacency_name : string
            Name of the adjacency graph to build.

        Returns
        -------
        nx.Graph
        """
        adjacency_list = self.adjacency_lists[adjacency_name].values
        
        edges_list = sum([
            [(i, j) for j in j_list]
            for i, j_list in zip(self.beds_ids, adjacency_list)
        ], start=[])

        beds_adjacency_graph = nx.Graph()
        beds_adjacency_graph.add_nodes_from(self.beds_ids)
        beds_adjacency_graph.add_edges_from(edges_list)

        return beds_adjacency_graph
