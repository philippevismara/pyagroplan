from __future__ import annotations

import numpy as np
import pandas as pd

from ._typing import FilePath


class PastCropPlan:
    """Handles past crop map data.

    Attributes
    ----------
    df_past_crop_map : pd.DataFrame
        DataFrame containing the raw crop map data (crop name, cropping dates, allocated beds, ...).

    Parameters
    ----------
    df_past_crop_map : pd.DataFrame
        DataFrame containing the raw crop map data (crop name, cropping dates, allocated beds, ...).
    """

    def __init__(
        self,
        df_past_crop_plan: pd.DataFrame | FilePath,
    ):
        from .data_loaders import CSVPastCropPlanLoader
        if isinstance(df_past_crop_plan, FilePath):
            df_past_crop_plan = CSVPastCropPlanLoader.load(df_past_crop_plan)
        df_past_crop_plan = df_past_crop_plan.copy()

        # TODO refactor and test date format before changing it
        from pandas._libs.tslibs.parsing import DateParseError
        try:
            df_past_crop_plan.starting_date = pd.to_datetime(
                df_past_crop_plan.starting_date,
            ).dt.date
            df_past_crop_plan.ending_date = pd.to_datetime(
                df_past_crop_plan.ending_date,
            ).dt.date
        except DateParseError:
            from .data_loaders.utils import starting_week_str_to_datetime, ending_week_str_to_datetime
            df_past_crop_plan.starting_date = starting_week_str_to_datetime(df_past_crop_plan.starting_date)
            df_past_crop_plan.ending_date = ending_week_str_to_datetime(df_past_crop_plan.ending_date)

        df_past_crop_plan.index = -(df_past_crop_plan.index+1)

        from .crop_calendar import _build_assignments_dataframe
        import numpy as np
        repeats = df_past_crop_plan["allocated_beds_ids"].apply(len)
        df_past_assignments = _build_assignments_dataframe(
            df_past_crop_plan,
            repeats=repeats,
            crop_ids=-(np.arange(np.sum(repeats))+1),
        )
        df_past_crop_calendar = df_past_crop_plan.copy()
        df_past_crop_calendar.drop(columns="allocated_beds_ids", inplace=True)
        df_past_crop_calendar["quantity"] = repeats

        gb = df_past_assignments.groupby("crop_group_id")
        allocated_bed_id = gb["allocated_beds_ids"].transform(lambda s: s.iloc[0])

        df_past_assignments.drop(columns="allocated_beds_ids", inplace=True)
        
        self.df_past_crop_plan = df_past_crop_plan
        self.df_past_assignments = df_past_assignments
        
        self.past_crop_calendar = df_past_assignments[["crop_name", "starting_date", "ending_date"]]
        self.df_past_crop_calendar = df_past_crop_calendar

        self.allocated_bed_id = allocated_bed_id

        self.n_assignments = len(df_past_assignments)

        self._check_consistency()


    def _check_consistency(self) -> None:
        cropping_intervals = self.df_past_assignments.loc[:, ["starting_date", "ending_date"]]
        from .utils.interval_graph import get_intervals_as_list_of_intervals
        get_intervals_as_list_of_intervals(cropping_intervals)

        assignments = self.allocated_bed_id

        issues = []
        bed_ids = np.unique(assignments)
        for bed_id in bed_ids:
            ind = np.where(assignments == bed_id)[0]
            data = self.df_past_assignments.loc[ind]
            data.sort_values(
                by=["starting_date", "ending_date"],
                inplace=True,
            )
            for i in range(len(data)-1):
                if data.iloc[i].loc["ending_date"] >= data.iloc[i+1].loc["starting_date"]:
                    issue = data.iloc[i:i+2].loc[:, ["crop_name", "starting_date", "ending_date"]]
                    issue["allocated_bed_id"] = bed_id
                    issues.append(issue)

        if issues:
            raise ValueError(
                "Inconsistent past crop plan, inconsistencies: \n"
                + "\n".join(map(repr, issues))
            )
