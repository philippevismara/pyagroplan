from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd


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

    def __init__(self, df_beds_data: pd.DataFrame):
        self.df_beds_data = df_beds_data.copy()
        self.beds_ids = df_beds_data["metadata"]["bed_id"].to_numpy().tolist()
        self.adjacency_lists = self.df_beds_data["adjacent_beds"]

        """
        def adjacency_function(i: int, j: int) -> bool:
            return j in self.adjacency_list.loc[i]
        self.adjacency_function = adjacency_function
        """

        self.n_beds = len(self.df_beds_data)

    def __str__(self) -> str:
        return """BedsData(n_beds={})""".format(self.n_beds)

    def __len__(self) -> int:
        return self.n_beds

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
