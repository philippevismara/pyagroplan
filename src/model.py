from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Generator

    from pychoco.variables.intvar import IntVar

    from .beds_data import BedsData
    from .constraints import Constraint
    from .crops_calendar import CropsCalendar
    from .solution import Solution

import numpy as np
from pychoco import Model

from .solution import Solution


class AgroEcoPlanModel:
    def __init__(self, crops_calendar: CropsCalendar, beds_data: BedsData, verbose: bool=False):
        self.crops_calendar = crops_calendar
        self.beds_data = beds_data
        self.n_assignments = self.crops_calendar.n_assignments
        self.n_beds = self.beds_data.n_beds
        self.verbose = verbose

        self.model = Model()
        """
        TODO add fixed domains (pre-allocated beds) + forbidden beds
        can't we add constraints instead? (less efficient?)
        """
        self.assignment_vars = self.model.intvars(self.n_assignments, 1, self.n_beds, name="a")
        self.assignment_vars = np.asarray(self.assignment_vars)

    def __str__(self) -> str:
        return "AgroEcoPlanModel(crop_calendar={}, beds_data={}, verbose={})".format(
            self.crops_calendar,
            self.beds_data,
            self.verbose,
        )

    def init(self, constraints: Sequence[Constraint]=tuple()) -> None:
        self._add_non_overlapping_assigments_constraints()
        self._break_symmetries()

        for constraint in constraints:
            self.add_constraint(constraint)

    def add_constraint(self, constraint: Constraint) -> None:
        constraints = constraint.build(self.model, self.assignment_vars)
        for cstr in constraints:
            cstr.post()

    def set_objective_function(self, variable: IntVar, maximize: bool) -> None:
        self.model.set_objective(variable, maximize)

    def configure_solver(self) -> None:
        # TODO allow to configurate solver
        self.solver = self.model.get_solver()

    def solve(self) -> Solution:
        has_solution = self.solver.solve()
        if not has_solution:
            raise RuntimeError("No solution found")
        else:
            return Solution(self.crops_calendar, self.assignment_vars)

    def iterate_over_all_solutions(self) -> Generator[Solution]:
        while True:
            try:
                yield self.solve()
            except RuntimeError:
                break

    def _add_non_overlapping_assigments_constraints(self) -> None:
        """
        TODO if the interval graph with rotations is chordal, allDifferent for all maximal cliques,
            and separators should be sufficient, but we should prove it to be sure.
        """
        for overlapping_crops in self.crops_calendar.crops_overlapping_cultivation_intervals:
            overlapping_assignment_vars = self.assignment_vars[list(overlapping_crops)]
            self.model.all_different(overlapping_assignment_vars).post()

    def _break_symmetries(self) -> None:
        for group in self.crops_calendar.crops_groups_assignments:
            # TODO remove len(group) == 1
            assert len(group) > 0
            group_vars = self.assignment_vars[group]
            self.model.increasing(group_vars, True).post()

    # TODO initNumberOfPositivePrecedences
    # TODO initNumberOfPositivePrecedencesCountBased
