import pytest
from pathlib import Path

import numpy as np
import pandas as pd

from pyagroplan.constraints import constraints as cstrs
from pyagroplan import AgroEcoPlanModel, CropPlanProblemData


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def crop_plan_problem_data():
    return CropPlanProblemData(
        beds_data=DATA_PATH / "beds_data_normal.csv",
        future_crop_calendar=DATA_PATH / "crop_calendar.csv",
        crop_types_attributes=DATA_PATH / "crop_types_attributes.csv",
    )


def test_forbid_negative_interactions_constraint(crop_plan_problem_data):
    df_spatial_interactions_matrix = pd.read_csv(
        DATA_PATH / "spatial_interactions_matrix.csv",
        sep=";",
        comment="#",
        index_col=0,
    )
    
    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    constraint = cstrs.ForbidNegativeInteractionsConstraint(
        crop_plan_problem_data,
        df_spatial_interactions_matrix,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_forbid_negative_interactions_subintervals_constraint(crop_plan_problem_data):
    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    df_spatial_interactions_matrix = pd.DataFrame(
        [
            ["", "+[1,-1][1,-1]", "+[1,-1][1,-1]"],
            ["+[1,-1][1,-1]", "", "-[1,-1][-2,-1]"],
            ["+[1,-1][1,-1]", "-[-2,-1][1,-1]", ""],
        ],
        index=["carotte", "tomate", "pomme_de_terre"],
        columns=["carotte", "tomate", "pomme_de_terre"],
    )
    df_spatial_interactions_matrix.index.name = "crop_type"

    constraint = cstrs.ForbidNegativeInteractionsSubintervalsConstraint(
        crop_plan_problem_data,
        df_spatial_interactions_matrix,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_dilute_species_constraint(crop_plan_problem_data):
    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    constraint = cstrs.DiluteSpeciesConstraint(
        crop_plan_problem_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_dilute_family_constraint(crop_plan_problem_data):
    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    constraint = cstrs.DiluteFamilyConstraint(
        crop_plan_problem_data,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_return_delays_constraint(crop_plan_problem_data):
    import pandas as pd
    df_return_delays = pd.DataFrame(
        [
            [5, 7, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        index=["carotte", "tomate", "pomme_de_terre"],
        columns=["carotte", "tomate", "pomme_de_terre"],
    )
    import datetime
    df_return_delays = df_return_delays.map(lambda i: datetime.timedelta(weeks=i))

    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    constraint = cstrs.ReturnDelaysConstraint(
        crop_plan_problem_data,
        df_return_delays,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_group_identical_crops_together_constraint(crop_plan_problem_data):
    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    constraint = cstrs.GroupIdenticalCropsTogetherConstraint(
        crop_plan_problem_data,
        crop_plan_problem_data.crop_calendar.future_crops_groups_assignments,
        adjacency_name="garden_neighbors",
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_crops_location_constraint(crop_plan_problem_data):
    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    def beds_selection_func(crop_data, beds_data):
        df_beds_attributes = beds_data._df_beds_data.attributes
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
        crop_plan_problem_data,
        beds_selection_func,
        forbidden=False,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]


def test_crops_precedences_constraint(crop_plan_problem_data):
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

    model = AgroEcoPlanModel(crop_plan_problem_data, verbose=False)

    constraint = cstrs.ForbidNegativePrecedencesConstraint(
        crop_plan_problem_data,
        df_precedences,
    )
    model.init([constraint])
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        assert constraint.check_solution(solution)[0]
