import pytest
from pathlib import Path

import constraints as cst
from model import AgroEcoPlanModel

from beds_data import BedsDataLoader
from crop_calendar import CropCalendarLoader


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data(beds_data_csv_filename):
    return BedsDataLoader.load(DATA_PATH / beds_data_csv_filename)


@pytest.fixture
def crop_calendar():
    return CropCalendarLoader.load(DATA_PATH / "crop_calendar.csv")


@pytest.mark.parametrize("beds_data_csv_filename", ["beds_data.csv"])
def test_agroecoplanmodel_no_constraints_no_solution(crop_calendar, beds_data):
    constraints = []

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()

    with pytest.raises(RuntimeError) as excinfo:
        model.solve()

    assert "No solution found" in str(excinfo.value)


@pytest.mark.parametrize("beds_data_csv_filename", ["beds_data_normal.csv"])
def test_agroecoplanmodel_no_constraints_with_solution(crop_calendar, beds_data):
    # TODO do some tests on solution
    constraints = []

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()

    solution = model.solve()
    assert len(solution) == 6
    print(solution)


"""
def test_agroecoplanmodel(crop_calendar, beds_data):
    constraints = [
        cst.CropRotationConstraint(),
        #constraints.DiluteSpeciesConstraint(),
    ]

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()
    print(model)
"""
