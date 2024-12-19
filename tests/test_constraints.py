import pytest
from pathlib import Path

import numpy as np

from src.constraints import constraints as cstrs
from src.data_loaders import CSVBedsDataLoader, CSVCropsCalendarLoader, CSVCropsDataLoader
from src.model import AgroEcoPlanModel


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data():
    return CSVBedsDataLoader.load(DATA_PATH / "beds_data_normal.csv")


@pytest.fixture
def crops_data():
    return CSVCropsDataLoader.load(
        DATA_PATH / "crops_metadata.csv",
        DATA_PATH / "crops_interactions.csv",
    )


@pytest.fixture
def crops_calendar(crops_data):
    return CSVCropsCalendarLoader.load(DATA_PATH / "crops_calendar.csv", crops_data)


def test_forbid_negative_interactions_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.ForbidNegativeInteractionsConstraint(crops_calendar, beds_data)
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values
        assert not beds_data.adjacency_function(crops_planning[5], crops_planning[3])
        assert not beds_data.adjacency_function(crops_planning[5], crops_planning[4])


def test_dilute_species_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.DiluteSpeciesConstraint(crops_calendar, beds_data)
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values

        assert not beds_data.adjacency_function(crops_planning[0], crops_planning[1])
        assert not beds_data.adjacency_function(crops_planning[1], crops_planning[2])
        assert not beds_data.adjacency_function(crops_planning[0], crops_planning[2])

        assert not beds_data.adjacency_function(crops_planning[3], crops_planning[4])


def test_dilute_family_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.DiluteFamilyConstraint(crops_calendar, beds_data)
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values

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
        crops_planning = solution.crops_planning["assignment"].values

        assert len(np.intersect1d(crops_planning[:3], crops_planning[6:7])) == 0


def test_group_identical_crops_together_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.GroupIdenticalCropsTogetherConstraint(
        crops_calendar,
        beds_data,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values

        assert beds_data.adjacency_function(crops_planning[0], crops_planning[1])
        assert beds_data.adjacency_function(crops_planning[1], crops_planning[2])

        assert beds_data.adjacency_function(crops_planning[3], crops_planning[4])


def test_crops_location_constraint(crops_calendar, beds_data):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    def beds_selection_func(crop_data, beds_data):
        df_beds = beds_data.df_beds_data
        beds_ids = np.asarray(beds_data.beds_ids)

        match crop_data["besoin_lumiere"]:
            case "ombre":
                return beds_ids[
                    (df_beds["ombre_ete"] == "oui")
                    & (df_beds["ombre_hiver"] == "oui")
                ]
            case "mi-ombre":
                return beds_ids[
                    df_beds["ombre_ete"] != df_beds["ombre_hiver"]
                ]
            case "soleil":
                return beds_ids[
                    (df_beds["ombre_ete"] == "non")
                    & (df_beds["ombre_hiver"] == "non")
                ]
            case _:
                return []

    constraint = cstrs.LocationConstraint(
        crops_calendar,
        beds_data,
        beds_selection_func,
        forbidden=False,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values

        # Tomatos in the sun
        assert crops_planning[3] in [3, 6]
        assert crops_planning[4] in [3, 6]

        # Potatoes and carrots in sun/shade
        assert crops_planning[0] in [2, 4, 5]
        assert crops_planning[1] in [2, 4, 5]
        assert crops_planning[2] in [2, 4, 5]
        assert crops_planning[5] in [2, 4, 5]
        assert crops_planning[6] in [2, 4, 5]
