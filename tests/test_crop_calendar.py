import numpy as np
import pandas as pd

from crop_calendar import CropCalendar


def test_crop_calendar():
    df_crop_calendar = pd.DataFrame(
        [
            ["Carotte", 1, 5, 3],
            ["Tomate", 3, 9, 2],
            ["Pomme de terre", 10, 12, 1],
        ],
        columns=["culture", "debut", "fin", "quantite"],
    )

    crop_calendar = CropCalendar(df_crop_calendar)

    assert crop_calendar.n_assignments == 6

    expected_groups = [
        [0, 1, 2],
        [3, 4],
        [5, ],
    ]
    for group, expected_group in zip(crop_calendar.crops_groups_assignments, expected_groups):
        np.testing.assert_array_equal(group, expected_group)

    assert crop_calendar.overlapping_assignments == frozenset((
        frozenset((0, 1, 2, 3, 4)),
        frozenset((5,)),
    ))
