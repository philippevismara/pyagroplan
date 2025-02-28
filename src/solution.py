from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from .crop_calendar import CropCalendar

import numpy as np
import pandas as pd


class Solution:
    """One assignment solution of the model.

    Attributes
    ----------
    crop_calendar : CropsCalendar
        Crops calendar used in the model.
    assignments : Sequence[int]
        Assignments of crops to beds.

    Parameters
    ----------
    crop_calendar : CropsCalendar
        Crops calendar used in the model.
    assignments : Sequence[int]
        Assignments of crops to beds.
    """

    def __init__(self, crop_calendar: CropCalendar, assignments: Sequence[int]):
        self.crop_calendar = crop_calendar
        self.assignments = assignments

        self.crops_planning = pd.DataFrame({
            "crop_id": self.crop_calendar.df_assignments["crop_id"],
            "crop_name": self.crop_calendar.df_assignments["crop_name"],
            "starting_date": self.crop_calendar.df_assignments["starting_date"],
            "ending_date": self.crop_calendar.df_assignments["ending_date"],
            "assignment": np.asarray(assignments, dtype=int),
        })
        self.crops_planning.sort_index(inplace=True)

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
