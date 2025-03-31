import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.crop_calendar import CropCalendar

CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def df_crop_calendar():
    df_crop_calendar = pd.DataFrame(
        [
            ["carotte", "carotte", "2020-W01", "2020-W05", 3],
            ["tomate", "tomate", "2020-W03", "2020-W09", 2],
            ["pomme_de_terre", "pomme_de_terre", "2020-W08", "2020-W12", 1],
            ["carotte", "carotte", "2020-W10", "2020-W12", 1],
            ["pomme_de_terre", "pomme_de_terre", "2020-W08", "2020-W09", 1],
        ],
        columns=[
            "crop_name",
            "crop_type",
            "starting_date",
            "ending_date",
            "quantity",
        ],
    )
    return df_crop_calendar


def test_crop_calendar_loader(df_crop_calendar):
    crop_calendar1 = CropCalendar(DATA_PATH / "crop_calendar.csv")
    crop_calendar2 = CropCalendar(df_crop_calendar)

    assert (crop_calendar1.df_crop_calendar == crop_calendar2.df_crop_calendar).all(axis=None)


def test_crop_calendar(df_crop_calendar):
    crop_calendar = CropCalendar(df_crop_calendar)

    assert crop_calendar.n_assignments == 8

    expected_groups = [
        [0, 1, 2],
        [3, 4],
        [5, ],
        [6, ],
        [7, ],
    ]

    for group, expected_group in zip(crop_calendar.crops_groups_assignments, expected_groups):
        np.testing.assert_array_equal(group, expected_group)

    assert crop_calendar.crops_overlapping_cultivation_intervals == frozenset((
        frozenset((0, 1, 2, 3, 4)),
        frozenset((3, 4, 5, 6)),
        frozenset((6, 7)),
    ))
