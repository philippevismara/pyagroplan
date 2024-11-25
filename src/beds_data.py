from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd


class BedsData:
    def __init__(self, df_beds_data: pd.DataFrame):
        self.df_beds_data = df_beds_data.copy()
        self.beds_ids = np.asarray(df_beds_data.index.array).tolist()
        self.adjacency_matrix = self.df_beds_data["adjacent_beds_ids"]

        def adjacency_function(i: int, j: int) -> bool:
            return j in self.adjacency_matrix.loc[i]
        self.adjacency_function = adjacency_function

        self.n_beds = len(self.df_beds_data)

    def __str__(self) -> str:
        return """BedsData(n_beds={})""".format(self.n_beds)

    def __len__(self) -> int:
        return self.n_beds

    def get_adjacency_graph(self) -> nx.Graph:
        edges_list = sum([
            [(i, j) for j in j_list]
            for i, j_list in self.adjacency_matrix.items()
        ], start=[])

        beds_adjacency_graph = nx.Graph()
        beds_adjacency_graph.add_nodes_from(self.adjacency_matrix.index.values)
        beds_adjacency_graph.add_edges_from(edges_list)

        return beds_adjacency_graph
