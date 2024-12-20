import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.crops_calendar import CropsCalendar
from src.data_loaders import CSVCropsCalendarLoader

CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def df_crops_calendar():
    df_crops_calendar = pd.DataFrame(
        [
            ["carotte", "carotte", 1, 5, 3],
            ["tomate", "tomate", 3, 9, 2],
            ["pomme_de_terre", "pomme_de_terre", 8, 12, 1],
            ["carotte", "carotte", 10, 12, 1],
            ["pomme_de_terre", "pomme_de_terre", 8, 9, 1],
        ],
        columns=["crop_name", "category", "starting_week", "ending_week", "allocated_beds_quantity"],
    )
    return df_crops_calendar.sort_values(by="starting_week")


def test_crops_calendar_loader(df_crops_calendar):
    crops_calendar = CSVCropsCalendarLoader.load(DATA_PATH / "crops_calendar.csv")

    assert (crops_calendar.df_crops_calendar == df_crops_calendar).all(axis=None)


def test_crops_calendar(df_crops_calendar):
    crops_calendar = CropsCalendar(df_crops_calendar)

    assert crops_calendar.n_assignments == 8

    expected_groups = [
        [0, 1, 2],
        [3, 4],
        [5, ],
        [6, ],
    ]
    for group, expected_group in zip(crops_calendar.crops_groups_assignments, expected_groups):
        np.testing.assert_array_equal(group, expected_group)

    assert crops_calendar.crops_overlapping_cultivation_intervals == frozenset((
        frozenset((0, 1, 2, 3, 4)),
        frozenset((3, 4, 5, 6)),
        frozenset((5, 7)),
    ))
