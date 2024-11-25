from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from collections.abc import Sequence

    import pandas as pd
    from pychoco.constraints import Constraint as ChocoConstraint
    from pychoco.variables import IntVar

    from ..beds_data import BedsData
    from ..crops_calendar import CropsCalendar
    from ..model import Model

from abc import ABC, abstractmethod

import networkx as nx


class Constraint(ABC):
    @abstractmethod
    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence: ...


class LocationConstraint(Constraint):
    def __init__(
            self,
            crops_calendar: CropsCalendar,
            beds_data: BedsData,
            beds_selection_func: Callable[[pd.Series, BedsData], Sequence[int] | Sequence[bool]],
            forbidden: bool = False,
    ):
        self.crops_calendar = crops_calendar
        self.beds_data = beds_data
        self.beds_selection_func = beds_selection_func
        self.forbidden = forbidden

    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for crop_var, (_, crop_data) in zip(assignment_vars, self.crops_calendar.df_assignments.iterrows()):
            crop_selected_beds = self.beds_selection_func(crop_data, self.beds_data)

            if len(crop_selected_beds) > 0:
                crop_selected_beds = list(map(int, crop_selected_beds))

                if self.forbidden:
                    crop_constraints = model.not_member(crop_var, crop_selected_beds)
                else:
                    crop_constraints = model.member(crop_var, crop_selected_beds)

                constraints.append(crop_constraints)

        return constraints


class SuccessionConstraint(Constraint):
    def __init__(
            self,
            crops_calendar: CropsCalendar,
            temporal_adjacency_graph: nx.Graph,
            forbidden: bool,
    ):
        self.crops_calendar = crops_calendar
        self.temporal_adjacency_graph = temporal_adjacency_graph
        self.forbidden = forbidden

    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for i in self.temporal_adjacency_graph:
            for j in self.temporal_adjacency_graph.neighbors(i):
                if self.forbidden:
                    constraints.append(
                        assignment_vars[i] != assignment_vars[j]
                    )
                else:
                    constraints.append(
                        assignment_vars[i] == assignment_vars[j]
                    )

        return constraints


# Switch from binary to nary constraint
class BinaryNeighbourhoodConstraint(Constraint):
    def __init__(
            self,
            crops_calendar: CropsCalendar,
            adjacency_graph: nx.Graph,
            forbidden: bool,
    ):
        self.crops_calendar = crops_calendar
        self.adjacency_graph = adjacency_graph
        self.forbidden = forbidden

    @abstractmethod
    def crops_selection_function(self, i: int, j: int) -> bool: ...

    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        # itertools.combination
        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    self.crops_calendar.is_overlapping_cultures((i, j))
                    and self.crops_selection_function(i, j)
                ):
                    tuples = []
                    for val1 in a_i.get_domain_values():
                        for val2 in self.adjacency_graph.neighbors(val1): # more general adjacency criteria? (node distance higher than 1? sharing the same connected component?)
                            tuples.append((val1, val2))

                    constraints.append(
                        model.table([a_i, a_j], tuples, feasible=not self.forbidden)
                    )

        return constraints


class GroupNeighbourhoodConstraint(Constraint):
    def __init__(
            self,
            crops_groups: Sequence[Sequence[int]],
            adjacency_graph: nx.Graph,
            forbidden: bool,
    ):
        self.crops_groups = crops_groups
        self.adjacency_graph = adjacency_graph
        self.forbidden = forbidden

    def build(self, model: Model, assignment_variables: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for crops_group in self.crops_groups:
            assert len(crops_group) > 0
            if len(crops_group) == 1:
                continue

            # TODO assumes first element in crops_group is lowest crop_id
            a_i = assignment_variables[crops_group[0]]
            crops_group_assignment_vars = [assignment_variables[i] for i in crops_group]

            allowed_tuples = []
            for val1 in a_i.get_domain_values():
                candidate_paths = nx.all_simple_paths(
                    self.adjacency_graph,
                    source=val1,
                    target=self.adjacency_graph.nodes,
                    cutoff=len(crops_group),
                )
                candidate_paths = list(filter(lambda p: len(p) == len(crops_group), candidate_paths))

                allowed_tuples += candidate_paths

            constraints.append(
                model.table(crops_group_assignment_vars, allowed_tuples, feasible=not self.forbidden)
            )

        return constraints
