import numpy as np
import pytest
from pathlib import Path

from src.model import AgroEcoPlanModel
from src.data_loaders import CSVBedsDataLoader, CSVCropCalendarLoader, CSVPastCropPlanLoader


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


@pytest.fixture
def beds_data(beds_data_csv_filename):
    return CSVBedsDataLoader.load(DATA_PATH / beds_data_csv_filename)


@pytest.fixture
def with_past_crop_plan():
    return False

@pytest.fixture
def crop_calendar(with_past_crop_plan):
    past_crop_plan = None
    if with_past_crop_plan:
        past_crop_plan = CSVPastCropPlanLoader.load(DATA_PATH / "past_crop_plan.csv")

    return CSVCropCalendarLoader.load(
        DATA_PATH / "crop_calendar.csv",
        past_crop_plan=past_crop_plan,
    )


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

    assert model.n_assignments == (0+8)
    assert len(model.past_crop_plan_vars) == 0
    assert len(model.future_assignment_vars) == 8
    
    model.init(constraints)
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())

    assert len(solutions) > 0

    for solution in solutions:
        crops_planning = solution.crops_planning["assignment"].values
        assert len(np.intersect1d(crops_planning[:3], crops_planning[3:5])) == 0
        assert len(np.intersect1d(crops_planning[3:5], crops_planning[5:6])) == 0
        assert len(np.intersect1d(crops_planning[5:6], crops_planning[6:7])) == 0


@pytest.mark.parametrize("beds_data_csv_filename", ["beds_data_normal.csv"])
@pytest.mark.parametrize("with_past_crop_plan", [True])
def test_agroecoplanmodel_with_past_crop_plan_no_constraints_with_solution(crop_calendar, beds_data):
    constraints = []

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose=False)

    assert model.n_assignments == (7+8)
    assert len(model.past_crop_plan_vars) == 7
    assert len(model.future_assignment_vars) == 8
    
    model.init(constraints)
    model.configure_solver()
    solutions = list(model.iterate_over_all_solutions())
    
    assert len(solutions) > 0

    for solution in solutions:
        # Check that past crops are correctly assigned        
        past_crop_plan = solution.past_crops_planning["assignment"].values
        assert (past_crop_plan[:3] == np.asarray([1, 2, 4])).all()
        assert (past_crop_plan[3:5] == np.asarray([4, 5])).all()
        assert (past_crop_plan[5:7] == np.asarray([3, 5])).all()

        crops_planning = solution.future_crops_planning["assignment"].values
        assert len(np.intersect1d(crops_planning[:3], crops_planning[3:5])) == 0
        assert len(np.intersect1d(crops_planning[3:5], crops_planning[5:6])) == 0
        assert len(np.intersect1d(crops_planning[5:6], crops_planning[6:7])) == 0
