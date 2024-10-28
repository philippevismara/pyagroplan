from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from .crops_data import CropsData

import networkx as nx
import numpy as np
import pandas as pd

from .interval_graph import interval_graph


class CropsCalendar:
    def __init__(self, df_crops_calendar: pd.DataFrame, crops_data: Optional[CropsData]=None):
        self.df_crops_calendar = df_crops_calendar.copy()
        self.crops_data = crops_data

        if self.crops_data is not None:
            self.df_crops_calendar = pd.merge(
                self.df_crops_calendar,
                self.crops_data.df_metadata,
                how="left",
                left_on="crop_name",
                right_index=True,
            )

        df = self.df_crops_calendar
        repeats = df["allocated_beds_quantity"].values.astype(int)
        self.crops_groups = np.repeat(df.index.values, repeats)
        df = df.loc[self.crops_groups]
        self.crops_groups_assignments = np.split(np.arange(len(df)), np.cumsum(repeats)[:-1])
        df.drop(columns="allocated_beds_quantity", inplace=True)
        self.crops_calendar = df[["crop_name", "starting_week", "ending_week"]].values

        self.crops_names = df["crop_name"].array

        self.df_assignments = df

        self.n_assignments = len(self.crops_calendar)

        self._interval_graph = interval_graph(list(map(list, self.crops_calendar[:,1:].astype(int))))
        self.crops_overlapping_cultivation_intervals = frozenset(
            frozenset(node for node in clique)
            for clique in nx.chordal_graph_cliques(self._interval_graph)
        )

    def __str__(self) -> str:
        return "CropsCalendar(n_crops={}, n_assignments={})".format(
            len(self.df_crops_calendar),
            self.n_assignments,
        )
