import pytest
from pathlib import Path

import numpy as np

import constraints as cstrs
from beds_data import BedsDataLoader
from crops_calendar import CropsCalendarLoader
from crops_data import CropsDataLoader
from model import AgroEcoPlanModel


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data():
    return BedsDataLoader.load(DATA_PATH / "beds_data_normal.csv")


@pytest.fixture
def crops_data():
    return CropsDataLoader.load(
        DATA_PATH / "crops_metadata.csv",
        DATA_PATH / "crops_interactions.csv",
    )


@pytest.fixture
def crops_calendar(crops_data):
    return CropsCalendarLoader.load(DATA_PATH / "crops_calendar.csv", crops_data)


def test_abstract_constraint():
    with pytest.raises(TypeError):
        cstrs.Constraint()


@pytest.mark.parametrize("implementation", ["table", "distance"])
def test_forbid_negative_interactions_constraint(crops_calendar, beds_data, implementation):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.ForbidNegativeInteractionsConstraint(
        crops_calendar, beds_data, implementation
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"]
        assert not beds_data.adjacency_function(crops_planning[5], crops_planning[3])
        assert not beds_data.adjacency_function(crops_planning[5], crops_planning[4])


def test_dilute_species_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.DiluteSpeciesConstraint(
        crops_calendar, beds_data
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"]

        assert not beds_data.adjacency_function(crops_planning[0], crops_planning[1])
        assert not beds_data.adjacency_function(crops_planning[1], crops_planning[2])
        assert not beds_data.adjacency_function(crops_planning[0], crops_planning[2])

        assert not beds_data.adjacency_function(crops_planning[3], crops_planning[4])


def test_dilute_family_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.DiluteFamilyConstraint(
        crops_calendar, beds_data
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"]

        assert not beds_data.adjacency_function(crops_planning[0], crops_planning[1])
        assert not beds_data.adjacency_function(crops_planning[1], crops_planning[2])
        assert not beds_data.adjacency_function(crops_planning[0], crops_planning[2])

        assert not beds_data.adjacency_function(crops_planning[3], crops_planning[4])
        assert not beds_data.adjacency_function(crops_planning[3], crops_planning[5])
        assert not beds_data.adjacency_function(crops_planning[4], crops_planning[5])


def test_crops_rotation_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.CropsRotationConstraint(
        crops_calendar
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"]

        assert len(np.intersect1d(crops_planning[:3], crops_planning[6:7])) == 0
