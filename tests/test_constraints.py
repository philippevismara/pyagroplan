import pytest
from pathlib import Path

import numpy as np

from src.constraints import constraints as cstrs
from src.data_loaders import CSVBedsDataLoader, CSVCropCalendarLoader, CSVCropsDataLoader
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
def crop_calendar(crops_data):
    return CSVCropCalendarLoader.load(DATA_PATH / "crop_calendar.csv", crops_data)


def test_forbid_negative_interactions_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.ForbidNegativeInteractionsConstraint(
        crop_calendar,
        beds_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_forbid_negative_interactions_subintervals_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    import pandas as pd
    crop_calendar.crops_data.df_interactions = pd.DataFrame(
        [
            ["", "+[1,-1][1,-1]", "+[1,-1][1,-1]"],
            ["+[1,-1][1,-1]", "", "-[1,-1][-2,-1]"],
            ["+[1,-1][1,-1]", "-[-2,-1][1,-1]", ""],
        ],
        index=["carotte", "tomate", "pomme_de_terre"],
        columns=["carotte", "tomate", "pomme_de_terre"],
    )

    constraint = cstrs.ForbidNegativeInteractionsSubintervalsConstraint(
        crop_calendar,
        crop_calendar.crops_data.df_interactions,
        beds_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_dilute_species_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.DiluteSpeciesConstraint(
        crop_calendar,
        beds_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_dilute_family_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.DiluteFamilyConstraint(
        crop_calendar,
        beds_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_family_crops_rotation_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.FamilyCropsRotationConstraint(
        crop_calendar
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_crop_types_rotation_constraint(crop_calendar, beds_data):
    import pandas as pd
    df_return_delays = pd.DataFrame(
        [
            [5, 0, 0],
            [7, 0, 0],
            [0, 0, 0],
        ],
        index=["carotte", "tomate", "pomme_de_terre"],
        columns=["carotte", "tomate", "pomme_de_terre"],
    )

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.CropTypesRotationConstraint(
        crop_calendar,
        df_return_delays,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_group_identical_crops_together_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.GroupIdenticalCropsTogetherConstraint(
        crop_calendar,
        beds_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_crops_location_constraint(crop_calendar, beds_data):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    def beds_selection_func(crop_data, beds_data):
        df_beds_attributes = beds_data.df_beds_data.attributes
        beds_ids = np.asarray(beds_data.beds_ids)

        match crop_data["besoin_lumiere"]:
            case "ombre":
                return beds_ids[
                    (df_beds_attributes["ombre_ete"] == "oui")
                    & (df_beds_attributes["ombre_hiver"] == "oui")
                ]
            case "mi-ombre":
                return beds_ids[
                    df_beds_attributes["ombre_ete"] != df_beds_attributes["ombre_hiver"]
                ]
            case "soleil":
                return beds_ids[
                    (df_beds_attributes["ombre_ete"] == "non")
                    & (df_beds_attributes["ombre_hiver"] == "non")
                ]
            case _:
                return []

    constraint = cstrs.LocationConstraint(
        crop_calendar,
        beds_data,
        beds_selection_func,
        forbidden=False,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_crops_precedences_constraint(crop_calendar, beds_data):
    import pandas as pd
    df_precedences = pd.DataFrame(
        [
            [-10, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        index=["carotte", "tomate", "pomme_de_terre"],
        columns=["carotte", "tomate", "pomme_de_terre"],
    )

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.ForbidNegativePrecedencesConstraint(
        crop_calendar,
        df_precedences,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]
