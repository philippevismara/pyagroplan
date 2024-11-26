from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pychoco import Model
    from pychoco.variables.variable import Variable
    from pychoco.variables.intvar import IntVar

    from .beds_data import BedsData
    from .crops_calendar import CropsCalendar

from abc import ABC, abstractmethod


class ObjectiveFunction(ABC):
    @abstractmethod
    def build_objective(self, model: Model, assignment_vars: Sequence[IntVar]) -> Variable: ...


class MaximizeNumberOfPositiveIteractionsObjective(ObjectiveFunction):
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData):
        self.crops_calendar = crops_calendar
        self.beds_data = beds_data

        self.crops_names = crops_calendar.crops_names
        self.crops_overlapping_intervals = (
            crops_calendar.crops_overlapping_cultivation_intervals
        )
        self.crops_interactions = crops_calendar.crops_data.crops_interactions

        self.lower_bound = 0
        self.upper_bound = self._compute_objective_maximum()

    def _compute_objective_maximum(self) -> int:
        raise NotImplementedError()

    def build_objective(self, model: Model, assignment_vars: Sequence[IntVar]) -> IntVar:
        n_assignments = len(assignment_vars)
        obj_var = model.intvar(self.lower_bound, self.upper_bound)
        adj_var = model.intvars((n_assignments, n_assignments), lb=0, ub=1)

        i = 0
        model.element(adj_var[i], adjacency_matrix[i], j).post()

        """
        for i in range(n_assignments):
            for j in range(n_assignments):
                adj_var[i,j] = self.adjency(i,j)
        """

        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                        any(
                            frozenset((i, j)) <= interval
                            for interval in self.crops_overlapping_intervals
                        )
                        and self.crops_interactions(
                            self.crops_names[i], self.crops_names[j]
                        ) >= 0
                ):
                    forbidden_tuples = []
                    for val1 in a_i.get_domain_values():
                        for val2 in self.beds_data.adjacency_matrix[val1]:
                            forbidden_tuples.append((val1, val2))
                            constraints.append(
                                model.table([a_i, a_j], forbidden_tuples, feasible=False)
                            )

        return obj_var


class MaximizeNumberOfPositivePrecedences(ObjectiveFunction):
    ...
