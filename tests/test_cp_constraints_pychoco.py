import pytest
from pathlib import Path

from pyagroplan import CropPlanProblemData
from pyagroplan.constraints import cp_constraints_pychoco as cstrs
from pyagroplan.constraints import constraints as cstrs2
from pyagroplan.solution import Solution



CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def crop_plan_problem_data():
    return CropPlanProblemData(
        beds_data=DATA_PATH / "beds_data_normal.csv",
        future_crop_calendar=DATA_PATH / "crop_calendar.csv",
        crop_types_attributes=DATA_PATH / "crop_types_attributes.csv",
    )


def test_abstract_constraint():
    with pytest.raises(TypeError):
        cstrs.Constraint()


def test_succession_constraint_solution_checking(crop_plan_problem_data):
    import pandas as pd
    df_return_delays = pd.DataFrame(
        [
            [5, 52, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        index=["carotte", "tomate", "pomme_de_terre"],
        columns=["carotte", "tomate", "pomme_de_terre"],
    )
    import datetime
    df_return_delays = df_return_delays.map(lambda i: datetime.timedelta(weeks=i))

    constraint = cstrs2.ReturnDelaysConstraint(
        crop_plan_problem_data,
        df_return_delays,
    )

    solution1 = Solution(
        crop_plan_problem_data,
        [
            0, 1, 2,
            3, 4,
            0,
            1,
            2,
        ],
    )
    assert constraint.check_solution(solution1)[0]

    solution2 = Solution(
        crop_plan_problem_data,
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
        crop_plan_problem_data,
        [
            0, 1, 2,
            3, 4,
            0,
            3,
            1,
        ],
    )
    assert constraint.check_solution(solution3)[0]
