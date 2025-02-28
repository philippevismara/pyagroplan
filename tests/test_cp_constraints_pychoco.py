import pytest
from pathlib import Path

from src.constraints import cp_constraints_pychoco as cstrs
from src.constraints import constraints as cstrs2
from src.data_loaders import CSVBedsDataLoader, CSVCropCalendarLoader, CSVCropsDataLoader
from src.solution import Solution



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


def test_abstract_constraint():
    with pytest.raises(TypeError):
        cstrs.Constraint()


def test_succession_constraint_solution_checking(crop_calendar):
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

    constraint = cstrs2.CropTypesRotationConstraint(
        crop_calendar,
        df_return_delays,
    )

    solution1 = Solution(
        crop_calendar,
        [0, 1, 2, 3, 4, 0, 1, 2],
    )
    assert constraint.check_solution(solution1)[0]

    solution2 = Solution(
        crop_calendar,
        [
            0, 1, 2,
            3, 4,
            0,
            1,
            3,
        ],
    )
    assert not constraint.check_solution(solution2)[0]

    solution3 = Solution(
        crop_calendar,
        [
            0, 1, 2,
            3, 4,
            0,
            3,
            1,
        ],
    )
    assert constraint.check_solution(solution3)[0]
