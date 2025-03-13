from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from collections.abc import Sequence

    from .past_crop_plan import PastCropPlan

import networkx as nx
import numpy as np
import pandas as pd

from .utils.interval_graph import interval_graph
from ._typing import FilePath


def _build_assignments_dataframe(
    df_crop_calendar: pd.DataFrame,
    repeats: np.ndarray,
    crop_ids: Optional[np.ndarray]=None,
) -> pd.DataFrame:
    crops_groups = np.repeat(df_crop_calendar.index.values, repeats)
    
    df_assignments = df_crop_calendar.loc[crops_groups]
    df_assignments.reset_index(names="crop_group_id", inplace=True)

    df_assignments.reset_index(names="crop_id", inplace=True)
    if crop_ids is not None:
        df_assignments["crop_id"] = crop_ids

    return df_assignments


class CropCalendar:
    """Handles crops data.

    Attributes
    ----------
    df_future_crop_calendar : pd.DataFrame
        DataFrame containing the raw crops calendar.
    crops_data : CropsData or None
        Crops metadata.
    crops_groups : np.array
    crops_groups_assignments : list[np.array]
    crop_calendar : np.array
    crops_names : np.array
    df_assignments : pd.DataFrame
        DataFrame containing the raw crops calendar with a single line per bed to allocate.
    n_assignments : int
        Total number of assignments to make.
    crops_overlapping_cultivation_intervals : frozenset[frozenset]
        Set of sets of groups of crops being cultivated at the same time.

    Parameters
    ----------
    df_future_crop_calendar : pd.DataFrame
        DataFrame containing the raw crops calendar.
    """

    def __init__(
        self,
        df_future_crop_calendar: pd.DataFrame | FilePath,
        df_crop_types_attributes: Optional[pd.DataFrame | FilePath] = None,
        past_crop_plan: Optional[PastCropPlan] = None,
    ):
        if isinstance(df_future_crop_calendar, FilePath):
            from .data_loaders import CSVCropCalendarLoader
            df_future_crop_calendar = CSVCropCalendarLoader.load(df_future_crop_calendar)
        df_future_crop_calendar = df_future_crop_calendar.copy()

        # TODO refactor and test date format before changing it
        from pandas._libs.tslibs.parsing import DateParseError
        try:
            df_future_crop_calendar.starting_date = pd.to_datetime(
                df_future_crop_calendar.starting_date,
            ).dt.date
            df_future_crop_calendar.ending_date = pd.to_datetime(
                df_future_crop_calendar.ending_date,
            ).dt.date
        except DateParseError:
            from .data_loaders.utils import starting_week_str_to_datetime, ending_week_str_to_datetime
            df_future_crop_calendar.starting_date = starting_week_str_to_datetime(df_future_crop_calendar.starting_date)
            df_future_crop_calendar.ending_date = ending_week_str_to_datetime(df_future_crop_calendar.ending_date)

        df_crop_calendar = df_future_crop_calendar.copy()

        df_crop_calendar = df_crop_calendar.sort_values(
            by=["starting_date", "ending_date", "crop_name", "quantity"],
        )

        df_assignments = _build_assignments_dataframe(
            df_crop_calendar.drop(columns="quantity"),
            repeats=df_crop_calendar["quantity"].values.astype(int),
        )
        n_future_assignments = len(df_assignments)

        if past_crop_plan is not None:
            df_crop_calendar = pd.concat((
                past_crop_plan.df_past_crop_calendar,
                df_crop_calendar,
            ))
            df_crop_calendar.reset_index(drop=True, inplace=True)

            df_assignments = pd.concat((
                past_crop_plan.df_past_assignments,
                df_assignments,
            ))
            df_assignments.reset_index(drop=True, inplace=True)

        if df_crop_types_attributes is not None:
            if isinstance(df_crop_types_attributes, FilePath):
                from .data_loaders import CSVCropTypesAttributesLoader
                df_crop_types_attributes = \
                    CSVCropTypesAttributesLoader.load(df_crop_types_attributes)

            intersection = np.setdiff1d(
                df_assignments["crop_type"].values,
                df_crop_types_attributes["crop_type"].values,
            )
            if len(intersection):
                raise RuntimeError(
                    f"missing some crop types in df_crop_type_attributes: {intersection}"
                )

            df_crop_calendar = pd.merge(
                df_crop_calendar,
                df_crop_types_attributes,
                how="left",
                on="crop_type",
                validate="many_to_one",
            )
            df_assignments = pd.merge(
                df_assignments,
                df_crop_types_attributes,
                how="left",
                on="crop_type",
                validate="many_to_one",
            )

        self.df_crop_calendar = df_crop_calendar
        self.df_crop_types_attributes = df_crop_types_attributes

        self.df_future_crop_calendar = df_future_crop_calendar
        self.past_crop_plan = past_crop_plan

        self.global_starting_date = df_future_crop_calendar.starting_date.min()
        
        self.df_assignments = df_assignments
        self.n_assignments = len(df_assignments)
        self.df_future_assignments = df_assignments.iloc[-n_future_assignments:]
        self.n_future_assignments = n_future_assignments

        self.crops_groups = df_assignments["crop_group_id"]
        self.crops_groups_assignments = list(df_assignments.groupby("crop_group_id").indices.values())
        
        self.crop_calendar = df_assignments[["crop_name", "starting_date", "ending_date"]]
        self.crops_names = df_assignments["crop_name"].array

        self.cropping_intervals = self.crop_calendar.loc[:, ["starting_date", "ending_date"]]
        self.future_cropping_intervals = self.cropping_intervals[self.cropping_intervals["ending_date"] >= self.global_starting_date]

        self._interval_graph = interval_graph(
            self.future_cropping_intervals,
            node_ids=self.future_cropping_intervals.index,
        )
        self.crops_overlapping_cultivation_intervals = frozenset(
            nx.chordal_graph_cliques(self._interval_graph)
        )

    def __str__(self) -> str:
        return "CropsCalendar(n_crops={}, n_assignments={})".format(
            len(self.df_crop_calendar),
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
        return any(
            frozenset(crops_ids) <= interval
            for interval in self.crops_overlapping_cultivation_intervals
        )

    def overlapping_cultures_iter(self, subset_size: int = 2) -> list[tuple[int]]:
        """Generates tuples of crops that are being cultivated at the same time.

        Parameters
        ----------
        subset_size : int (default: 2)
            Size of the subsets of overlapping crops to generate (by default generate pairs of overlapping crops).

        Returns
        -------
        list of tuples of ints
        """
        from itertools import combinations
        overlapping_subsets = [
            overlapping_subset
            for clique in self.crops_overlapping_cultivation_intervals
            for overlapping_subset in combinations(clique, subset_size)
        ]
        return sorted(set(overlapping_subsets))
