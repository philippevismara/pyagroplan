from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..beds_data import BedsData
    from ..crops_calendar import CropsCalendar

from .cp_constraints_pychoco import BinaryNeighbourhoodConstraint, GroupNeighbourhoodConstraint, SuccessionConstraint, LocationConstraint


class CropsRotationConstraint(SuccessionConstraint):
    """Enforces crops rotation based on a return delay.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    """
    def __init__(self, crops_calendar: CropsCalendar):
        self.return_delay = crops_calendar.df_assignments["return_delay"].values
        self.families = crops_calendar.df_assignments["crop_family"].values

        intervals = crops_calendar.crops_calendar[:, 1:3]
        intervals[:, -1] += self.return_delay
        from ..utils.interval_graph import interval_graph
        temporal_adjacency_graph = interval_graph(
            list(map(list, intervals)),
            filter_func=lambda i,j: self.families[i] == self.families[j],
        )

        super().__init__(crops_calendar, temporal_adjacency_graph, forbidden=True)


class ForbidNegativeInteractionsConstraint(BinaryNeighbourhoodConstraint):
    """Forbids negative interactions between crops.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    beds_data : BedsData
    """
    def __init__(
            self,
            crops_calendar: CropsCalendar,
            beds_data: BedsData,
    ):
        adjacency_graph = beds_data.get_adjacency_graph()
        super().__init__(crops_calendar, adjacency_graph, forbidden=True)

        if not crops_calendar.crops_data:
            raise ValueError("No crops interaction data can be found")
        self.crops_interactions = crops_calendar.crops_data.crops_interactions
        self.crops_names = crops_calendar.crops_names

    def crops_selection_function(self, i: int, j: int) -> bool:
        """Selects only pairs of crops with negative interactions.

        :meta private:
        """
        return self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0  # type: ignore[no-any-return]


class DiluteSpeciesConstraint(BinaryNeighbourhoodConstraint):
    """Forbids crops from identical species to be spatially adjacent.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    beds_data : BedsData
    """
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        adjacency_graph = beds_data.get_adjacency_graph()
        super().__init__(crops_calendar, adjacency_graph, forbidden=True)
        self.crops_species = crops_calendar.crops_names

    def crops_selection_function(self, i: int, j: int) -> bool:
        """Selects only pairs of crops from identical species.

        :meta private:
        """
        return self.crops_species[i] == self.crops_species[j] # type: ignore[no-any-return]


class DiluteFamilyConstraint(BinaryNeighbourhoodConstraint):
    """Forbids crops from identical family to be spatially adjacent.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    beds_data : BedsData
    """
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        adjacency_graph = beds_data.get_adjacency_graph()
        super().__init__(crops_calendar, adjacency_graph, forbidden=True)
        self.crops_families = crops_calendar.df_assignments["crop_family"].array

    def crops_selection_function(self, i: int, j: int) -> bool:
        """Selects only pairs of crops from identical family.

        :meta private:
        """
        return self.crops_families[i] == self.crops_families[j] # type: ignore[no-any-return]


class GroupIdenticalCropsTogetherConstraint(GroupNeighbourhoodConstraint):
    """Enforces crops from same crop group to be spatially close.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    beds_data : BedsData
    """
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        adjacency_graph = beds_data.get_adjacency_graph()
        groups = crops_calendar.crops_groups_assignments
        super().__init__(groups, adjacency_graph, forbidden=False)
