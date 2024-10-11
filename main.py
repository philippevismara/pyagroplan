import argparse

import numpy as np
from pychoco import Model

import constraints
from beds_data import BedsDataLoader
from crop_calendar import CropCalendarLoader


class Solution:
    def __init__(self, variables):
        self.variables = variables
        self.values = {var.name: var.get_value() for var in variables}
        # TODO self.variables = choco_solution.retrieveIntVars()

    def __str__(self):
        return "Solution: {}".format(self.values)

    def to_csv(self, filename):
        raise NotImplementedError()


class AgroEcoPlanModel:
    def __init__(self, crop_calendar, beds_data, verbose=False):
        self.crop_calendar = crop_calendar
        self.beds_data = beds_data
        self.n_assignments = self.crop_calendar.n_assignments
        self.n_beds = self.beds_data.n_beds
        self.verbose = verbose

        self.model = Model()
        self.assignment_vars = None

    def __str__(self):
        return "AgroEcoPlanModel(crop_calendar={}, beds_data={}, verbose={})".format(
            self.crop_calendar,
            self.beds_data,
            verbose,
        )

    def init(self, constraints=None):
        self._init_variables()
        self._add_non_overlapping_assigments_constraints()
        self._break_symmetries()

        for constraint in constraints:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        constraint.post(self.model)

    def configure_solver(self):
        # TODO allow to configurate solver
        self.solver = self.model.get_solver()

    def solve(self):
        return self.solver.solve()

    def get_solution(self):
        return Solution(self.assignment_vars)

    def _init_variables(self):
        """
        TODO add fixed domains (pre-allocated beds) + forbidden beds
        can't we add constraints instead? (less efficient?)
        """
        self.assignment_vars = self.model.intvars(self.n_assignments, 1, self.n_beds, name="a")
        self.assignment_vars = np.asarray(self.assignment_vars)

    def _add_non_overlapping_assigments_constraints(self):
        """
        TODO if the interval graph with rotations is chordal, allDifferent for all maximal cliques,
            and separators should be sufficient, but we should prove it to be sure.
        """
        for overlapping_assignments in self.crop_calendar.overlapping_assignments:
            overlapping_assignment_vars = self.assignment_vars[list(overlapping_assignments)]
            self.model.all_different(overlapping_assignment_vars).post()

    def _break_symmetries(self):
        for group in self.crop_calendar.crops_groups_assignments:
            # TODO remove len(group) == 1
            assert len(group) > 0
            group_vars = self.assignment_vars[group]
            self.model.increasing(group_vars, True).post()

    # TODO initNumberOfPositivePrecedences
    # TODO initNumberOfPositivePrecedencesCountBased


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agroecological crop allocation problem solver",
    )

    args = parser.parse_args()

    crop_calendar_filename = "data/crop_calendar_1an_v7.csv"
    beds_data_filename = "data/beds_data.csv"
    verbose = True

    crop_calendar = CropCalendarLoader.load(crop_calendar_filename)
    beds_data = BedsDataLoader.load(beds_data_filename)

    constraints = [
        #constraints.CropRotationConstraint(),
        #constraints.DiluteSpeciesConstraint(),
    ]

    print(crop_calendar)
    print(beds_data)
    print(constraints)

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose)
    model.init(constraints)
    model.configure_solver()
    print(model)

    model.solve()
    solution = model.get_solution()
    print(solution)
