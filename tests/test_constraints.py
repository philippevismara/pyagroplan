import pytest
from pathlib import Path

import constraints as cstrs
from beds_data import BedsDataLoader
from crops_calendar import CropsCalendarLoader
from crops_data import CropsDataLoader
from model import AgroEcoPlanModel


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data():
    return BedsDataLoader.load(DATA_PATH / "beds_data_normal.csv")


@pytest.fixture
def crops_data():
    return CropsDataLoader.load(DATA_PATH / "crops_interactions.csv")


@pytest.fixture
def crops_calendar(crops_data):
    return CropsCalendarLoader.load(DATA_PATH / "crops_calendar.csv", crops_data)


def test_abstract_constraint():
    with pytest.raises(TypeError):
        cstrs.Constraint()


@pytest.mark.parametrize("implementation", ["table", "distance"])
def test_forbid_negative_interactions_constraint(crops_calendar, beds_data, implementation):
    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)

    constraint = cstrs.ForbidNegativeInteractionsConstraint(
        crops_calendar, beds_data, implementation
    )
    model.init([constraint])
    model.configure_solver()

    for solution in model.iterate_over_all_solutions():
        crops_planning = solution.crops_planning["assignment"]
        assert not beds_data.adjacency_function(crops_planning[5], crops_planning[3])
        assert not beds_data.adjacency_function(crops_planning[5], crops_planning[4])
