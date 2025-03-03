from __future__ import annotations

import pandas as pd


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
        df_past_crop_plan: pd.DataFrame,
    ):
        df_past_crop_plan = df_past_crop_plan.copy()

        # TODO refactor and test date format before changing it
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

        # TODO split every allocated beds or not?
        allocated_beds_ids = df_past_assignments["allocated_beds_ids"]

        df_past_assignments.drop(columns="allocated_beds_ids", inplace=True)
        
        self.df_past_crop_plan = df_past_crop_plan
        self.df_past_assignments = df_past_assignments
        
        self.past_crop_calendar = df_past_assignments[["crop_name", "starting_date", "ending_date"]]

        self.allocated_beds_ids = allocated_beds_ids

        self.n_assignments = len(df_past_assignments)
