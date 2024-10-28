from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pychoco.variables import Variable, IntVar

    from beds_data import BedsData
    from crops_calendar import CropsCalendar
    from model import Model

from abc import ABC, abstractmethod


class ObjectiveFunction(ABC):
    @abstractmethod
    def build_objective(self, model: Model) -> Variable: ...


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

    def build_objective(self, model: Model) -> IntVar:
        assignment_vars = model.assignment_vars
        obj_var = model.intvar(self.lower_bound, self.upper_bound)

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
