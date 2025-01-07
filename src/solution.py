from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from .crops_calendar import CropsCalendar

import pandas as pd


class Solution:
    """One assignment solution of the model.

    Attributes
    ----------
    crops_calendar : CropsCalendar
        Crops calendar used in the model.
    variables : Sequence[IntVar]
        Variables of the model.
    crops_planning : pd.DataFrame
        Solution as a `DataFrame` with two columns with the crop name and

    Parameters
    ----------
    crops_calendar : CropsCalendar
        Crops calendar used in the model.
    assignments : Sequence[int]
        Variables of the model.
    """

    def __init__(self, crops_calendar: CropsCalendar, assignments: Sequence[int]):
        self.crops_calendar = crops_calendar
        self.assignments = assignments

        self.crops_planning = pd.DataFrame({
            "crop_name": self.crops_calendar.df_assignments["crop_name"],
            "starting_week": self.crops_calendar.df_assignments["starting_week"],
            "ending_week": self.crops_calendar.df_assignments["ending_week"],
            "assignment": assignments,
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
