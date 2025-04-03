from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from .._typing import FilePath

import numpy as np
import pandas as pd

from .beds_data import BedsData
from .crop_calendar import CropCalendar
from .past_crop_plan import PastCropPlan


class CropPlanProblemData:
    def __init__(
        self,
        beds_data: BedsData | pd.DataFrame | FilePath,
        future_crop_calendar: pd.DataFrame | FilePath,
        past_crop_plan: Optional[PastCropPlan | pd.DataFrame | FilePath] = None,
        crop_types_attributes: Optional[pd.DataFrame | FilePath] = None,
    ):
        if not isinstance(beds_data, BedsData):
            beds_data = BedsData(beds_data)

        if past_crop_plan is not None and not isinstance(past_crop_plan, PastCropPlan):
            past_crop_plan = PastCropPlan(past_crop_plan)

        crop_calendar = CropCalendar(
            future_crop_calendar,
            past_crop_plan=past_crop_plan,
            df_crop_types_attributes=crop_types_attributes,
        )

        self._check_enough_beds_for_crop_calendar(beds_data, crop_calendar)
        self._check_consistency_in_past_allocated_beds_ids(beds_data, crop_calendar)
        
        self.beds_data = beds_data
        self.crop_calendar = crop_calendar


    def _check_enough_beds_for_crop_calendar(
        self,
        beds_data: BedsData,
        crop_calendar: CropCalendar,
    ) -> None:
        n_beds_min = max(map(len, crop_calendar.crops_overlapping_cultivation_intervals))
        n_available_beds = len(beds_data)

        if n_available_beds < n_beds_min:
            raise ValueError(
                f"Inconsistency: not enough beds available "
                f"({n_available_beds} beds available, {n_beds_min} needed)"
            )


    def _check_consistency_in_past_allocated_beds_ids(
        self,
        beds_data: BedsData,
        crop_calendar: CropCalendar,
    ) -> None:
        if crop_calendar.past_crop_plan is None:
            return

        past_allocated_beds_ids = crop_calendar.past_crop_plan.allocated_bed_id
        available_beds_ids = beds_data.beds_ids
        isin = np.isin(past_allocated_beds_ids, available_beds_ids)
        if (~isin).any():
            unknown_beds_ids = past_allocated_beds_ids[~isin]
            raise ValueError(
                f"Inconsistency in past allocated beds ids with beds data: "
                f"beds with id {list(unknown_beds_ids)} not found in beds data"
            )
