import numpy as np
import pandas as pd
import pytest

from pyagroplan.exceptions import IntervalError
from pyagroplan.data import PastCropPlan


def test_past_crop_plan():
    df_past_crop_plan = pd.DataFrame(
        [
            ["carotte", "carotte", "2020-W01", "2020-W05", [0, 1]],
            ["tomate", "tomate", "2020-W03", "2020-W09", [2]],
        ],
        columns=[
            "crop_name",
            "crop_type",
            "starting_date",
            "ending_date",
            "allocated_beds_ids",
        ],
    )
    past_crop_plan = PastCropPlan(df_past_crop_plan)

    assert past_crop_plan.n_assignments == 3
    np.testing.assert_equal(past_crop_plan.allocated_bed_id.values, [0, 1, 2])


def test_past_crop_plan_wrong_interval():
    df_past_crop_plan = pd.DataFrame(
        [
            ["carotte", "carotte", "2020-W01", "2020-W05", [0, 1]],
            ["tomate", "tomate", "2020-W10", "2020-W09", [2]],
        ],
        columns=[
            "crop_name",
            "crop_type",
            "starting_date",
            "ending_date",
            "allocated_beds_ids",
        ],
    )
    with pytest.raises(IntervalError):
        PastCropPlan(df_past_crop_plan)


def test_past_crop_plan_inconsistent():
    df_past_crop_plan = pd.DataFrame(
        [
            ["carotte", "carotte", "2020-W01", "2020-W05", [0, 1]],
            ["tomate", "tomate", "2020-W03", "2020-W09", [1]],
        ],
        columns=[
            "crop_name",
            "crop_type",
            "starting_date",
            "ending_date",
            "allocated_beds_ids",
        ],
    )
    with pytest.raises(ValueError):
        PastCropPlan(df_past_crop_plan)
