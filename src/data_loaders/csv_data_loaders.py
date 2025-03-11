from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._typing import FilePath

import pandas as pd

from .utils import convert_string_to_int_list, dispatch_to_appropriate_loader

from ..beds_data import BedsData
from ..crop_calendar import CropCalendar
from ..past_crop_plan import PastCropPlan

N_WEEKS_PER_YEAR = 52


class CSVDataLoader:
    @classmethod
    def load(cls, filename: FilePath) -> pd.DataFrame:
        df_data = dispatch_to_appropriate_loader(filename, cls)
        return df_data


class CSVBedsDataLoader(CSVDataLoader):
    data_cls = BedsData

    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
            header=[0, 1],
        )

        df.loc[:, ("adjacent_beds", slice(None))] = \
            df.loc[:, ("adjacent_beds", slice(None))].map(convert_string_to_int_list)

        return df


class CSVPastCropPlanLoader(CSVDataLoader):
    data_cls = PastCropPlan

    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            converters={
                "allocated_beds_ids": convert_string_to_int_list,
            },
            comment="#",
        )
        return df


class CSVCropCalendarLoader(CSVDataLoader):
    data_cls = CropCalendar

    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
        )
        return df


class CSVCropTypesAttributesLoader(CSVDataLoader):
    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
        )
        return df
