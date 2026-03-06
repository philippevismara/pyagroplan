from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..._typing import FilePath

import pandas as pd

from .loaders_utils import convert_string_to_int_list, dispatch_to_appropriate_loader

from ..beds_data import BedsData
from ..crop_calendar import CropCalendar
from ..past_crop_plan import PastCropPlan


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
            dtype={"id": int},
            # converters={'adjacent_beds': lambda x: tuple(map(int, x.split(',')))},
            skip_blank_lines=True,
        )
        df = df.astype("object")

        df.loc[:, ("adjacent_beds", slice(None))] = df.loc[
            :, ("adjacent_beds", slice(None))
        ].map(convert_string_to_int_list)

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
            skip_blank_lines=True,
        )
        df = df.astype("object")
        return df


class CSVCropCalendarLoader(CSVDataLoader):
    data_cls = CropCalendar

    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(filename, sep=";", comment="#", skip_blank_lines=True)
        df = df.astype("object")
        return df


class CSVCropTypesAttributesLoader(CSVDataLoader):
    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(filename, sep=";", comment="#", skip_blank_lines=True)
        df = df.astype("object")
        return df


class CSVReturnDelaysLoader(CSVDataLoader):
    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        # TODO allow for years and weeks units
        df = pd.read_csv(
            filename, sep=";", comment="#", index_col=0, skip_blank_lines=True
        )

        df.fillna(0, inplace=True)
        df *= 52  # Number of weeks per year

        import datetime

        df = df.map(lambda i: datetime.timedelta(weeks=i))

        df = df.astype("object")
        return df
