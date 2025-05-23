from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from . import CropPlanProblemData

import numpy as np


class Solution:
    """One assignment solution of the model.

    Attributes
    ----------
    crop_plan_problem_data : CropPlanProblemData
        Crops calendar and beds data used in the model.
    assignments : Sequence[int]
        Assignments of crops to beds.

    Parameters
    ----------
    crop_plan_problem_data : CropPlanProblemData
        Crops calendar and beds data used in the model.
    assignments : Sequence[int]
        Assignments of crops to beds.
    """

    def __init__(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        assignments: Sequence[int],
    ):
        crop_calendar = crop_plan_problem_data.crop_calendar

        crops_planning = crop_calendar.df_assignments[[
            "crop_id", "crop_group_id", "crop_name", "starting_date", "ending_date"
        ]].copy()
        crops_planning["assignment"] = np.asarray(assignments, dtype=int)
        crops_planning.sort_index(inplace=True)

        self.crop_plan_problem_data = crop_plan_problem_data
        self.assignments = assignments
        self.crops_planning = crops_planning
        self.past_crops_planning = crops_planning.iloc[:-crop_calendar.n_future_assignments]
        self.future_crops_planning = crops_planning.iloc[-crop_calendar.n_future_assignments:]

    def __len__(self) -> int:
        return len(self.crops_planning)

    def __str__(self) -> str:
        return "Solution:\n{}".format(self.crops_planning)

    def to_csv(self, filename: str, **kwargs: Any) -> None:
        """Saves the solution as a CSV file.

        Parameters
        ----------
        filename : str
            CSV filename to use.
        kwargs
            arguments to pass to panda's CSV writer
        """
        kwargs = {
            "index": False,
            "sep": ";",
        } | kwargs
        self.crops_planning.to_csv(filename, **kwargs)
