from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from . import CropPlanProblemData

import numpy as np

from enum import Enum

class SolverStatus(Enum):
        FEASIBLE = "feasible"     # a solution has been found
        INFEASIBLE = "infeasible" # no solution can be found (over-constrained problem)
        TIMEOUT = "timeout"       # no solution found before search limits reached (e.g., time limit, memory limit, etc.)
        OPTIMAL = "optimal"       # an optimal solution has been found (i.e., the best solution according to the objective function)


class Solution:
    """One assignment solution of the model.

    Attributes
    ----------
    crop_plan_problem_data : CropPlanProblemData
        Crops calendar and beds data used in the model.
    assignments : Sequence[int]
        Assignments of crops to beds.
    status : SolverStatus
        Status of the solution (e.g., FEASIBLE, INFEASIBLE, TIMOUT, etc.).

    Parameters
    ----------
    crop_plan_problem_data : CropPlanProblemData
        Crops calendar and beds data used in the model.
    assignments : Sequence[int]
        Assignments of crops to beds.
    """

            
    OPTIMAL = SolverStatus.OPTIMAL
    FEASIBLE = SolverStatus.FEASIBLE
    INFEASIBLE = SolverStatus.INFEASIBLE
    TIMEOUT = SolverStatus.TIMEOUT


    def __init__(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        assignments: Sequence[int],
        status: SolverStatus = SolverStatus.FEASIBLE,
    ):
        self.status = status

        if self.status !=Solution.FEASIBLE:
        
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
        else:   
            self.crop_plan_problem_data = crop_plan_problem_data
            self.assignments = assignments
            self.crops_planning = None
            self.past_crops_planning = None
            self.future_crops_planning = None

    def __bool__(self) -> bool:
        return self.status == Solution.FEASIBLE

    def __len__(self) -> int:
        if self.crops_planning is None:
            return 0
        return len(self.crops_planning)

    def __str__(self) -> str:
        if self.status == Solution.FEASIBLE:
            return "Solution:\n{}".format(self.crops_planning)
        else:
            return "Solution not found: {}".format(self.status.value)

    def to_csv(self, filename: str, **kwargs: Any) -> None:
        """Saves the solution as a CSV file.

        Parameters
        ----------
        filename : str
            CSV filename to use.
        kwargs
            arguments to pass to panda's CSV writer
        """
        if self.crops_planning is None:
            raise ValueError("No solution to save: {}".format(self.status.value))
        kwargs = {
            "index": False,
            "sep": ";",
        } | kwargs
        self.crops_planning.to_csv(filename, **kwargs)
