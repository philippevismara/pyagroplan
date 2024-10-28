import pandas as pd
import pytest
from pathlib import Path

from beds_data import BedsData, CSVBedsDataLoader

CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def df_beds_data():
    df_beds_data = pd.DataFrame(
        [
            [1, (2,)],
            [2, (1, 3)],
            [3, (2,)],
        ],
        columns=["bed_id", "adjacent_beds_ids"],
    )
    df_beds_data.set_index("bed_id", inplace=True)
    return df_beds_data


def test_beds_loader(df_beds_data):
    beds_data = CSVBedsDataLoader.load(DATA_PATH / "beds_data.csv")
    assert (beds_data.df_beds_data == df_beds_data).all(axis=None)


def test_beds_data(df_beds_data):
    beds_data = BedsData(df_beds_data)

    assert len(beds_data) == 3

    adjacency_function = beds_data.adjacency_function
    assert adjacency_function(1, 2)
    assert adjacency_function(2, 3)
    assert not adjacency_function(1, 3)
