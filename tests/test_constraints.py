import pytest
from pathlib import Path

import constraints as cstrs
from beds_data import BedsDataLoader
from crop_calendar import CropCalendarLoader
from crops_data import CropsDataLoader
from model import AgroEcoPlanModel


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data():
    return BedsDataLoader.load(DATA_PATH / "beds_data.csv")


@pytest.fixture
def crops_data():
    return CropsDataLoader.load(DATA_PATH / "crops_interactions.csv")


@pytest.fixture
def crop_calendar(crops_data):
    return CropCalendarLoader.load(DATA_PATH / "crop_calendar.csv", crops_data)


def test_abstract_constraint():
    with pytest.raises(TypeError):
        cstrs.Constraint()


@pytest.mark.parametrize("implementation", ["explicitly", "table", "distance"])
def test_forbid_negative_interactions_constraint(crop_calendar, beds_data, implementation):
    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    constraint = cstrs.ForbidNegativeInteractionsConstraint(
        crop_calendar, beds_data, implementation
    )
    model.init([constraint])
