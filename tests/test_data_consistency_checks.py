import pytest
from pathlib import Path

from pyagroplan import CropPlanProblemData


CURRENT_DIR = Path(__file__).parent.resolve()
DATA_PATH = CURRENT_DIR / "data"


def test_not_enough_beds_for_crop_calendar():
    with pytest.raises(ValueError) as excinfo:
        CropPlanProblemData(
            beds_data=DATA_PATH / "beds_data.csv",
            future_crop_calendar=DATA_PATH / "crop_calendar.csv",
        )

    assert "not enough beds available" in str(excinfo.value)
