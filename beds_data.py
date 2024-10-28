from __future__ import annotations

import pandas as pd


class CSVBedsDataLoader:
    @staticmethod
    def load(filename: str) -> BedsData:
        def list_converter(s: str) -> tuple[int,...]:
            str_list = s.split(",")

            if len(str_list) == 0 or len(str_list[0]) == 0:
                return tuple()
            else:
                return tuple(map(int, str_list))

        df_beds_data = pd.read_csv(
            filename,
            sep=";",
            converters={
                "planche_contact": list_converter
            },
            index_col="planche",
            comment="#",
        )
        df_beds_data.rename(columns={
            "planche": "bed_id",
            "planche_contact": "adjacent_beds_ids",
            "jardin": "garden_id",
        }, inplace=True)
        beds_data = BedsData(df_beds_data)
        return beds_data


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
