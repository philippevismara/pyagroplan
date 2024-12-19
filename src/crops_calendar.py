from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from collections.abc import Sequence

    from .crops_data import CropsData

import networkx as nx
import numpy as np
import pandas as pd

from .utils.interval_graph import interval_graph


class CropsCalendar:
    """Handles crops data.

    Attributes
    ----------
    df_crops_calendar : pd.DataFrame
        DataFrame containing the raw crops calendar.
    crops_data : CropsData or None
        Crops metadata.
    crops_groups : np.array
    crops_groups_assignments : list[np.array]
    crops_calendar : np.array
    crops_names : np.array
    df_assignments : pd.DataFrame
        DataFrame containing the raw crops calendar with a single line per bed to allocate.
    n_assignments : int
        Total number of assignments to make.
    crops_overlapping_cultivation_intervals : frozenset[frozenset]
        Set of sets of groups of crops being cultivated at the same time.

    Parameters
    ----------
    df_crops_calendar : pd.DataFrame
        DataFrame containing the raw crops calendar.
    crops_data : CropsData, optional
        Crops metadata object.
    """
    def __init__(self, df_crops_calendar: pd.DataFrame, crops_data: Optional[CropsData]=None):
        self.df_crops_calendar = df_crops_calendar.copy().sort_values(by="starting_week")
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

    def is_overlapping_cultures(self, crops_ids: Sequence[int]) -> bool:
        """Checks if crops are all being cultivated at the same time.

        Parameters
        ----------
        crops_ids : Sequence[int]

        Returns
        -------
        bool
            True if all crops are being cultivated at the same time (i.e., the intersection of their cultivation intervals is not the empty set).
        """
        assert len(crops_ids) >= 2
        return any(frozenset(crops_ids) <= interval for interval in self.crops_overlapping_cultivation_intervals)

    """
    # TODO
    def overlapping_cultures_iter(self, subset_size=None) -> bool:
        raise NotImplementedError()
    """
