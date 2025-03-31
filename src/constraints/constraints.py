from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ..beds_data import BedsData
    from ..crop_calendar import CropCalendar

    import pandas as pd

import datetime

from .cp_constraints_pychoco import (
    BinaryNeighbourhoodConstraint,
    GroupNeighbourhoodConstraint,
    SuccessionConstraint,
    SuccessionConstraintWithReinitialisation,
    LocationConstraint,
)
from ..utils.utils import timedelta_dataframe_to_directed_graph


class FamilyCropsRotationConstraint(SuccessionConstraint):
    """Enforces crops rotation based on a return delay for each botanical family.

    Parameters
    ----------
    crop_calendar : CropCalendar
    """

    def __init__(self, crop_calendar: CropCalendar):
        """
        TODO if the interval graph with rotations is chordal, allDifferent for all maximal cliques,
            and separators should be sufficient, but we should prove it to be sure.
        """
        # TODO get return delays with units from the start
        import pandas as pd
        return_delays = crop_calendar.df_assignments["return_delay"].values
        return_delays = pd.to_timedelta(return_delays, unit="W")

        families = crop_calendar.df_assignments["crop_family"].values

        intervals = crop_calendar.cropping_intervals.copy()
        intervals["ending_date"] = (pd.to_datetime(intervals.ending_date) + return_delays).dt.date
        is_future_crop = crop_calendar.df_assignments["is_future_crop"].values

        def filter_func(i: int, j: int) -> bool:
            return (
                (is_future_crop[i] or is_future_crop[j])
                and (families[i] == families[j])
            )
        
        from ..utils.interval_graph import interval_graph
        temporal_adjacency_graph = interval_graph(
            intervals,
            filter_func=filter_func,
            node_ids=list(intervals.index),
        )

        super().__init__(crop_calendar, temporal_adjacency_graph, forbidden=True)


class CropTypesRotationConstraint(SuccessionConstraint):
    """Enforces crops rotation based on a return delay matrix between crop types.

    Parameters
    ----------
    crop_calendar : CropCalendar
    return_delays : pd.DataFrame
        Matrix containing the return delays, an entry i,j corresponds to a return delay applied after a crop of type j (precedent crop) on crops of type i (following crop).
    """

    def __init__(self, crop_calendar: CropCalendar, return_delays: pd.DataFrame):
        # TODO get return delays with units from the start
        return_delays = return_delays.map(lambda i: datetime.timedelta(weeks=i))
        self.return_delays = return_delays

        crop_type_return_delays_graph = timedelta_dataframe_to_directed_graph(
            return_delays.T,
            name="return_delay",
        )
        intervals = crop_calendar.cropping_intervals
        starting_dates = crop_calendar.df_assignments["starting_date"].values
        crop_types = crop_calendar.df_assignments["crop_type"].values
        is_future_crop = crop_calendar.df_assignments["is_future_crop"].values
        
        def filter_func(i: int, j: int) -> bool:
            return (
                (is_future_crop[i] or is_future_crop[j])
                and (crop_types[i], crop_types[j]) in crop_type_return_delays_graph.edges
                and (
                    starting_dates[i]
                    + crop_type_return_delays_graph.edges[
                        crop_types[i],
                        crop_types[j]
                    ]["return_delay"]
                    >= starting_dates[j]
                )
            )
        from ..utils.interval_graph import build_graph
        temporal_adjacency_graph = build_graph(
            intervals,
            filter_func=filter_func,
            node_ids=list(intervals.index),
        )

        super().__init__(crop_calendar, temporal_adjacency_graph, forbidden=True)


class ForbidNegativeInteractionsConstraint(BinaryNeighbourhoodConstraint):
    """Forbids negative interactions between crops.

    Parameters
    ----------
    crop_calendar : CropCalendar
    df_crops_interactions_matrix: pd.DataFrame
        Matrix containing the interactions, a negative entry i,j corresponds to negative interaction between crop i and crop j.
    beds_data : BedsData
    adjacency_name : string
    """

    def __init__(
        self,
        crop_calendar: CropCalendar,
        df_crops_interactions_matrix: pd.DataFrame,
        beds_data: BedsData,
        adjacency_name: str,
    ):
        adjacency_graph = beds_data.get_adjacency_graph(adjacency_name)
        super().__init__(crop_calendar, adjacency_graph, forbidden=True)

        self.df_crops_interactions_matrix = df_crops_interactions_matrix
        categorisation_name = self.df_crops_interactions_matrix.index.name
        if categorisation_name:
            self.categorisation = crop_calendar.df_assignments[categorisation_name].values
        else:
            self.categorisation = crop_calendar.df_assignments.index.values

    def crops_selection_function(self, need_i: int, need_j: int) -> bool:
        """Selects only pairs of crops with negative interactions.

        :meta private:
        """
        return self.df_crops_interactions_matrix.loc[
            self.categorisation[need_i],
            self.categorisation[need_j]
        ] < 0  # type: ignore[no-any-return]


class ForbidNegativeInteractionsSubintervalsConstraint(BinaryNeighbourhoodConstraint):
    """Forbids negative interactions between crops using defined subintervals.

    Parameters
    ----------
    crop_calendar : CropCalendar
    df_crops_interactions_matrix: pd.DataFrame
        Matrix containing the interactions, an entry i,j corresponds to an interaction between crop i and crop j.
        It contains a string of the form "-[1,3][1,-1]", for instance, to forbid a spatial interaction between crop i during its 3 first week of cultivation and crop j during its whole cultivation period.
    beds_data : BedsData
    adjacency_name : string
    """

    def __init__(
        self,
        crop_calendar: CropCalendar,
        df_crops_interactions_matrix: pd.DataFrame,
        beds_data: BedsData,
        adjacency_name: str,
    ):
        adjacency_graph = beds_data.get_adjacency_graph(adjacency_name)
        super().__init__(crop_calendar, adjacency_graph, forbidden=True)

        self.df_crops_interactions_matrix = df_crops_interactions_matrix
        categorisation_name = self.df_crops_interactions_matrix.index.name
        if categorisation_name:
            self.categorisation = crop_calendar.df_assignments[categorisation_name].values
        else:
            self.categorisation = crop_calendar.df_assignments.index.values

        import re
        int_pattern = r"[+-]?[0-9]+"
        self.regex_prog = re.compile(
            rf"([\+-])\[({int_pattern}),({int_pattern})\]"
            rf"\[({int_pattern}),({int_pattern})\]"
        )

    def crops_selection_function(self, i: int, j: int) -> bool:
        """Selects only pairs of crops with negative interactions.

        :meta private:
        """
        interaction_str = self.df_crops_interactions_matrix.loc[
            self.categorisation[i],
            self.categorisation[j]
        ]

        # Checks if there is no constraint enforced in the matrix
        import numpy as np
        if (
            (isinstance(interaction_str, (float, np.floating)) and np.isnan(interaction_str))
            or (len(interaction_str) == 0)
        ):
            return False

        match = self.regex_prog.search(interaction_str)
        if not match:
            raise ValueError(
                f"Can not extract intervals from string: {interaction_str}"
            )

        sign, s1, e1, s2, e2 = match.groups()
        s1, e1, s2, e2 = int(s1), int(e1), int(s2), int(e2)

        if sign == "+":
            return False

        interval1, interval2 = (
            self.crop_calendar.df_assignments
            .iloc[[i, j]]
            .loc[:, ["starting_date", "ending_date"]]
            .values
        )

        interval1_final, interval2_final = interval1.copy(), interval2.copy()
        if s1 >= 0:
            interval1_final[0] = interval1[0] + datetime.timedelta(weeks=max(0, s1 - 1))
        else:
            interval1_final[0] = interval1[1] + datetime.timedelta(weeks=min(0, s1 + 1))
        if e1 >= 0:
            interval1_final[1] = interval1[0] + datetime.timedelta(weeks=max(0, e1 - 1))
        else:
            interval1_final[1] = interval1[1] + datetime.timedelta(weeks=min(0, e1 + 1))
        if s2 >= 0:
            interval2_final[0] = interval2[0] + datetime.timedelta(weeks=max(0, s2 - 1))
        else:
            interval2_final[0] = interval2[1] + datetime.timedelta(weeks=min(0, s2 + 1))
        if e2 >= 0:
            interval2_final[1] = interval2[0] + datetime.timedelta(weeks=max(0, e2 - 1))
        else:
            interval2_final[1] = interval2[1] + datetime.timedelta(weeks=min(0, e2 + 1))

        return (
            (interval1_final[0] <= interval2_final[1])
            and (interval1_final[1] >= interval2_final[0])
        )


class DiluteSpeciesConstraint(BinaryNeighbourhoodConstraint):
    """Forbids crops from identical species to be spatially adjacent.

    Parameters
    ----------
    crop_calendar : CropCalendar
    beds_data : BedsData
    adjacency_name: string
    """

    def __init__(
        self,
        crop_calendar: CropCalendar,
        beds_data: BedsData,
        adjacency_name: str,
    ):
        adjacency_graph = beds_data.get_adjacency_graph(adjacency_name)
        super().__init__(crop_calendar, adjacency_graph, forbidden=True)
        self.crops_species = crop_calendar.df_assignments["crop_name"].array

    def crops_selection_function(self, i: int, j: int) -> bool:
        """Selects only pairs of crops from identical species.

        :meta private:
        """
        return self.crops_species[i] == self.crops_species[j]  # type: ignore[no-any-return]


class DiluteFamilyConstraint(BinaryNeighbourhoodConstraint):
    """Forbids crops from identical family to be spatially adjacent.

    Parameters
    ----------
    crop_calendar : CropCalendar
    beds_data : BedsData
    adjacency_name : string
    """

    def __init__(
        self,
        crop_calendar: CropCalendar,
        beds_data: BedsData,
        adjacency_name: str,
    ):
        adjacency_graph = beds_data.get_adjacency_graph(adjacency_name)
        super().__init__(crop_calendar, adjacency_graph, forbidden=True)
        self.crops_families = crop_calendar.df_assignments["crop_family"].array

    def crops_selection_function(self, i: int, j: int) -> bool:
        """Selects only pairs of crops from identical family.

        :meta private:
        """
        return self.crops_families[i] == self.crops_families[j]  # type: ignore[no-any-return]


class GroupIdenticalCropsTogetherConstraint(GroupNeighbourhoodConstraint):
    """Enforces crops from same crop group to be spatially close.

    Parameters
    ----------
    crop_calendar : CropCalendar
    beds_data : BedsData
    adjacency_name : string
    """

    def __init__(
        self,
        crops_groups: Sequence[Sequence[int]],
        beds_data: BedsData,
        adjacency_name: str,
    ):
        adjacency_graph = beds_data.get_adjacency_graph(adjacency_name)
        super().__init__(crops_groups, adjacency_graph, forbidden=False)


class ForbidNegativePrecedencesConstraint(SuccessionConstraintWithReinitialisation):
    def __init__(self, crop_calendar: CropCalendar, precedences: pd.DataFrame):
        precedences_graph = timedelta_dataframe_to_directed_graph(
            precedences,
            name="precedence_effect_duration",
        )

        intervals = crop_calendar.cropping_intervals
        starting_dates = crop_calendar.df_assignments["starting_date"].values
        global_starting_date = crop_calendar.global_starting_date
        crop_types = crop_calendar.df_assignments["crop_type"].values

        def filter_func(i: int, j: int) -> bool:
            return (
                (global_starting_date <= max(starting_dates[i], starting_dates[j]))
                and (crop_types[i], crop_types[j]) in precedences_graph.edges
                and (precedences_graph.edges[crop_types[i], crop_types[j]]["weight"] <= 0)
                and (
                    starting_dates[i]
                    - datetime.timedelta(
                        weeks=precedences_graph.edges[crop_types[i], crop_types[j]]["weight"]
                    )
                    >= starting_dates[j]
                )
            )

        from ..utils.interval_graph import build_graph
        temporal_adjacency_graph = build_graph(
            intervals,
            filter_func=filter_func,
            node_ids=list(intervals.index),
        )
        super().__init__(crop_calendar, temporal_adjacency_graph, forbidden=True)
