import pandas as pd
import pytest
from pathlib import Path

from src.beds_data import BedsData
from src.data_loaders import CSVBedsDataLoader

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
        columns=pd.MultiIndex.from_tuples((
            ("metadata", "bed_id"),
            ("adjacent_beds", "garden_neighbors"),
        )),
    )
    return df_beds_data


def test_beds_loader(df_beds_data):
    df_beds_data_from_file = CSVBedsDataLoader.load(DATA_PATH / "beds_data.csv")
    assert (df_beds_data_from_file == df_beds_data).all(axis=None)


def test_beds_data(df_beds_data):
    beds_data = BedsData(df_beds_data)

    assert len(beds_data) == 3

    adjacency_graph = beds_data.get_adjacency_graph("garden_neighbors")
    assert (1, 2) in adjacency_graph.edges
    assert (2, 3) in adjacency_graph.edges
    assert (1, 3) not in adjacency_graph.edges
