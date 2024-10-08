import argparse

import numpy as np
import pandas as pd

import constraints


class AgroEcoPlanModel:
    def __init__(self):
        raise NotImplementedError()

    def init(self):
        pass

    def add_constraint(self, constraint):
        constraint.post(self.model)

    def _break_symmetries(self):
        pass

    def _init_interval_graphs(self):
        pass


class Solution:
    def __init__(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    def to_csv(self, filename):
        raise NotImplementedError()


class AgroEcoPlanProblemSolver:
    def __init__(self, crop_calendar, constraints, verbose):
        self.crop_calendar = crop_calendar
        self.constraints = constraints
        self.verbose = verbose

        df = crop_calendar
        df = df.iloc[np.repeat(np.arange(len(df)), df["quantite"].values)]
        df.drop(columns="quantite", inplace=True)
        self._crop_calendar = df[["culture", "debut", "fin"]].values

    def init_model(self):
        # init model
        # init assignment variables (with proper domain)
        # init interval graphs
        # find maximal cliques to add an all_different constraint

        raise NotImplementedError()

        self.break_symmetries()

    def break_symmetries(self):
        raise NotImplementedError()

    def configure(self):
        raise NotImplementedError()

    def solve(self):
        # TODO check model has been initialized
        raise NotImplementedError()

    # TODO initNumberOfPositivePrecedences
    # TODO initNumberOfPositivePrecedencesCountBased


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agroecological crop allocation problem solver",
    )

    args = parser.parse_args()

    crop_calendar_filename = "data/crop_calendar_1an_v7.csv"
    verbose = True

    df = pd.read_csv(crop_calendar_filename, sep=";")
    crop_calendar = df[["culture", "debut", "fin", "quantite"]]

    constraints = [
        constraints.CropRotationConstraint(),
        constraints.DiluteSpeciesConstraint(),
    ]

    print(crop_calendar)
    print(constraints)

    problem_solver = AgroEcoPlanProblemSolver(crop_calendar, constraints, verbose)
    problem_solver.init_model()
    solution = problem_solver.solve()

    print(solution)
