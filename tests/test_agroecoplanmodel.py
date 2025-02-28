import numpy as np
import pytest
from pathlib import Path

from src.model import AgroEcoPlanModel
from src.data_loaders import CSVBedsDataLoader, CSVCropCalendarLoader


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data(beds_data_csv_filename):
    return CSVBedsDataLoader.load(DATA_PATH / beds_data_csv_filename)


@pytest.fixture
def crop_calendar():
    return CSVCropCalendarLoader.load(DATA_PATH / "crop_calendar.csv")


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
    constraints = []

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values
        assert len(np.intersect1d(crops_planning[:3], crops_planning[3:5])) == 0
        assert len(np.intersect1d(crops_planning[3:5], crops_planning[5:6])) == 0
        assert len(np.intersect1d(crops_planning[5:6], crops_planning[6:7])) == 0

"""
def test_agroecoplanmodel(crop_calendar, beds_data):
    constraints = [
        cstrs.CropRotationConstraint(),
        #constraints.DiluteSpeciesConstraint(),
    ]

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)
    model.init(constraints)
    model.configure_solver()
    print(model)
"""
