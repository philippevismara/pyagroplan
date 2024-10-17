import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from crops_calendar import CropsCalendar, CropsCalendarLoader

CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def df_crops_calendar():
    df_crops_calendar = pd.DataFrame(
        [
            ["carotte", 1, 5, 3],
            ["tomate", 3, 9, 2],
            ["pomme_de_terre", 8, 12, 1],
        ],
        columns=["culture", "debut", "fin", "quantite"],
    )
    return df_crops_calendar


def test_crops_calendar_loader(df_crops_calendar):
    crops_calendar = CropsCalendarLoader.load(DATA_PATH / "crops_calendar.csv")

    assert (crops_calendar.df_crops_calendar == df_crops_calendar).all(axis=None)


def test_crops_calendar(df_crops_calendar):
    crops_calendar = CropsCalendar(df_crops_calendar)

    assert crops_calendar.n_assignments == 6

    expected_groups = [
        [0, 1, 2],
        [3, 4],
        [5, ],
    ]
    for group, expected_group in zip(crops_calendar.crops_groups_assignments, expected_groups):
        np.testing.assert_array_equal(group, expected_group)

    assert crops_calendar.crops_overlapping_cultivation_intervals == frozenset((
        frozenset((0, 1, 2, 3, 4)),
        frozenset((3, 4, 5)),
    ))
