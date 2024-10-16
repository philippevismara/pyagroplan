import numpy as np
import pytest
from pathlib import Path

from model import AgroEcoPlanModel

from beds_data import BedsDataLoader
from crops_calendar import CropsCalendarLoader


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data(beds_data_csv_filename):
    return BedsDataLoader.load(DATA_PATH / beds_data_csv_filename)


@pytest.fixture
def crops_calendar():
    return CropsCalendarLoader.load(DATA_PATH / "crops_calendar.csv")


@pytest.mark.parametrize("beds_data_csv_filename", ["beds_data.csv"])
def test_agroecoplanmodel_no_constraints_no_solution(crops_calendar, beds_data):
    constraints = []

    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()

    with pytest.raises(RuntimeError) as excinfo:
        model.solve()

    assert "No solution found" in str(excinfo.value)


@pytest.mark.parametrize("beds_data_csv_filename", ["beds_data_normal.csv"])
def test_agroecoplanmodel_no_constraints_with_solution(crops_calendar, beds_data):
    constraints = []

    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()

    for solution in model.iterate_over_all_solutions():
        crops_planning = solution.crops_planning["assignment"].values
        assert len(np.intersect1d(crops_planning[:3], crops_planning[3:5])) == 0
        assert len(np.intersect1d(crops_planning[5:], crops_planning[3:5])) == 0

"""
def test_agroecoplanmodel(crops_calendar, beds_data):
    constraints = [
        cstrs.CropRotationConstraint(),
        #constraints.DiluteSpeciesConstraint(),
    ]

    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()
    print(model)
"""
