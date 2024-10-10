import argparse

import numpy as np
import networkx as nx
import pandas as pd
from pychoco import Model

import constraints


class CropCalendar:
    def __init__(self, df_crop_calendar):
        self.df_crop_calendar = df_crop_calendar.copy()

        df = self.df_crop_calendar
        repeats = df["quantite"].values
        self.crops_groups = np.repeat(df.index.values, repeats)
        df = df.loc[self.crops_groups]
        self.crops_groups_assignments = np.split(np.arange(len(df)), np.cumsum(repeats)[:-1])
        df.drop(columns="quantite", inplace=True)
        self.crop_calendar = df[["culture", "debut", "fin"]].values

        self.n_assignments = len(self.crop_calendar)

        from interval_graph import interval_graph
        self._interval_graph = interval_graph(list(map(list, self.crop_calendar[:,1:].astype(int))))
        self._maximal_cliques = nx.chordal_graph_cliques(self._interval_graph)
        self.overlapping_assignments = list(list(node[0] for node in clique) for clique in self._maximal_cliques)

    def __str__(self):
        return """CropCalendar(n_crops={}, n_assignments={})""".format(len(self.df_crop_calendar), self.n_assignments)


class AgroEcoPlanModel:
    def __init__(self, crop_calendar, n_beds, verbose=False):
        # TODO add beds structure
        self.crop_calendar = crop_calendar
        self.n_assignments = self.crop_calendar.n_assignments
        self.n_beds = n_beds
        self.verbose = verbose

        self.model = Model()
        self.assignment_vars = None

    def __str__(self):
        return "AgroEcoPlanModel(crop_calendar={}, n_beds={}, verbose={})".format(crop_calendar, n_beds, verbose)

    def init(self, constraints=None):
        self._init_variables()
        self._add_non_overlapping_assigments_constraints()
        self._break_symmetries()

        for constraint in constraints:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        constraint.post(self.model)

    def solve(self):
        # TODO allow to configurate solver
        return self.model.get_solver().solve()

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
            overlapping_assignment_vars = self.assignment_vars[overlapping_assignments]
            self.model.all_different(overlapping_assignment_vars).post()

    def _break_symmetries(self):
        for group in self.crop_calendar.crops_groups_assignments:
            # TODO remove len(group) == 1
            assert len(group) > 0
            group_vars = self.assignment_vars[group]
            self.model.increasing(group_vars, True).post()

    # TODO initNumberOfPositivePrecedences
    # TODO initNumberOfPositivePrecedencesCountBased


class Solution:
    def __init__(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    def to_csv(self, filename):
        raise NotImplementedError()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agroecological crop allocation problem solver",
    )

    args = parser.parse_args()

    crop_calendar_filename = "data/crop_calendar_1an_v7.csv"
    n_beds = 80
    verbose = True

    df = pd.read_csv(crop_calendar_filename, sep=";")
    df_crop_calendar = df[["culture", "debut", "fin", "quantite"]]
    crop_calendar = CropCalendar(df_crop_calendar)

    constraints = [
        #constraints.CropRotationConstraint(),
        #constraints.DiluteSpeciesConstraint(),
    ]

    print(crop_calendar)
    print(constraints)

    model = AgroEcoPlanModel(crop_calendar, n_beds, verbose)
    model.init(constraints)
    print(model)

    solution = model.solve()
    print(solution)
