from __future__ import annotations

import pandas as pd


class BedsData:
    def __init__(self, df_beds_data: pd.DataFrame):
        self.df_beds_data = df_beds_data.copy()
        self.adjacency_matrix = self.df_beds_data["adjacent_beds_ids"]

        def adjacency_function(i: int, j: int) -> bool:
            return j in self.adjacency_matrix.loc[i]
        self.adjacency_function = adjacency_function

        self.n_beds = len(self.df_beds_data)

    def __str__(self) -> str:
        return """BedsData(n_beds={})""".format(self.n_beds)

    def __len__(self) -> int:
        return self.n_beds
