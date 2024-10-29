from __future__ import annotations
from typing import TYPE_CHECKING, no_type_check

if TYPE_CHECKING:
    from typing import Callable
    from collections.abc import Sequence

    import pandas as pd
    from pychoco.constraints.constraint import Constraint as ChocoConstraint
    from pychoco.variables.intvar import IntVar

    from .beds_data import BedsData
    from .crops_calendar import CropsCalendar
    from .model import Model

from abc import ABC, abstractmethod

from .interval_graph import interval_graph


class Constraint(ABC):
    @abstractmethod
    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence: ...


class UnitaryCropsBedsConstraint(Constraint):
    def __init__(
            self,
            crops_calendar: CropsCalendar,
            beds_data: BedsData,
            beds_selection_func: Callable[[pd.Series, BedsData], Sequence[int] | Sequence[bool]],
            forbidden: bool = True,
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

class CropsRotationConstraint(Constraint):
    def __init__(self, crops_calendar: CropsCalendar):
        self.crops_calendar = crops_calendar
        self.return_delay = self.crops_calendar.df_assignments["return_delay"].values
        self.families = self.crops_calendar.df_assignments["crop_family"].values

        intervals = self.crops_calendar.crops_calendar[:, 1:3]
        intervals[:, -1] += self.return_delay
        self.interval_graph = interval_graph(
            list(map(list, intervals)),
            filter_func=lambda i,j: self.families[i] == self.families[j],
        )

    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for i in self.interval_graph:
            for j in self.interval_graph.neighbors(i):
                constraints.append(
                    model.arithm(assignment_vars[i], "!=", assignment_vars[j])
                )

        return constraints


class ForbidNegativeInteractionsConstraint(Constraint):
    def __init__(
            self,
            crops_calendar: CropsCalendar,
            beds_data: BedsData,
            implementation: str="distance",
    ):
        if not crops_calendar.crops_data:
            raise ValueError("No crops interaction data can be found")

        self.crops_overlapping_intervals = crops_calendar.crops_overlapping_cultivation_intervals
        self.crops_interactions = crops_calendar.crops_data.crops_interactions
        self.crops_names = crops_calendar.crops_names
        self.beds_data = beds_data
        self.implementation = implementation

        build_funcs = {
            # "explicitly": self._build_explicitly,
            "table": self._build_table,
            "distance": self._build_distance,
        }
        if self.implementation not in build_funcs:
            raise ValueError()

        self.build_func = build_funcs[self.implementation]

    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        return self.build_func(model, assignment_vars)

    """
    def _build_explicitly(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        # TODO does this really work? (calling adjacency function with IntVars?)
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0
                ):
                    constraints.append(
                        self.beds_data.adjacency_function(a_i, a_j) == False
                    )

        return constraints
    """

    def _build_table(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0
                ):
                    forbidden_tuples = []
                    for val1 in a_i.get_domain_values():
                        for val2 in self.beds_data.adjacency_matrix[val1]:
                            forbidden_tuples.append((val1, val2))
                    constraints.append(
                        model.table([a_i, a_j], forbidden_tuples, feasible=False)
                    )

        return constraints

    def _build_distance(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        # TODO prune useless constraints manually (or automatically ?)
        # TODO stronger constraint then needed
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0
                ):
                    constraints.append(
                        model.distance(a_i, a_j, ">", 1)
                    )

        return constraints


class AdjacencyConstraint(Constraint):
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData, forbid: bool):
        self.crops_overlapping_intervals = crops_calendar.crops_overlapping_cultivation_intervals
        self.beds_data = beds_data
        self.forbid = forbid

    @abstractmethod
    def selection_function(self, i: int, j: int) -> bool: ...

    def build(self, model: Model, assignment_vars: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.selection_function(i, j)
                ):
                    tuples = []
                    for val1 in a_i.get_domain_values():
                        for val2 in self.beds_data.adjacency_matrix[val1]:
                            tuples.append((val1, val2))

                    constraints.append(
                        model.table([a_i, a_j], tuples, feasible=not self.forbid)
                    )

        return constraints


class DiluteSpeciesConstraint(AdjacencyConstraint):
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        super().__init__(crops_calendar, beds_data, forbid=True)
        self.crops_species = crops_calendar.crops_names

    def selection_function(self, i: int, j: int) -> bool:
        return self.crops_species[i] == self.crops_species[j] # type: ignore[no-any-return]


class DiluteFamilyConstraint(AdjacencyConstraint):
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        super().__init__(crops_calendar, beds_data, forbid=True)
        self.crops_families = crops_calendar.df_assignments["crop_family"].array

    def selection_function(self, i: int, j: int) -> bool:
        return self.crops_families[i] == self.crops_families[j] # type: ignore[no-any-return]


class GroupIdenticalCropsTogetherConstraint(Constraint):
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        self.crops_calendar = crops_calendar
        self.beds_data = beds_data

    def build(self, model: Model, assignment_variables: Sequence[IntVar]) -> Sequence[ChocoConstraint]:
        constraints = []

        for group in self.crops_calendar.crops_groups_assignments:
            # TODO remove len(group) == 1
            assert len(group) > 0
            """
            if len(group) == 1:
                continue
            """

            # TODO assumes first element in group is lowest crop_id
            a_i = assignment_variables[group[0]]
            group_assignment_vars = [assignment_variables[i] for i in group]

            # TODO assumes that adjacent beds have adjacent indices
            allowed_tuples = []
            for val1 in a_i.get_domain_values():
                possible_tuple = True
                for i in range(val1 + 1, val1 + len(group)):
                    if i not in self.beds_data.adjacency_matrix[i-1]:
                        possible_tuple = False
                        break

                if possible_tuple:
                    allowed_tuples.append(
                        list(range(val1, val1 + len(group)))
                    )

            constraints.append(
                model.table(group_assignment_vars, allowed_tuples, feasible=True)
            )

        return constraints

"""
TODO handle optimization objective
class InteractionConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model, assignment_vars):
        raise NotImplementedError()
"""


"""
TODO what is this constraint ? (added after paper)
class ForbidNegativePrecedencesConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model, assignment_vars):
        raise NotImplementedError()
"""


"""
TODO

public:
postInteractionReifTable
postInteractionReifBased

private:
postInteractionCountBased
postInteractionCustomPropBased
postInteractionGraphBased
"""
