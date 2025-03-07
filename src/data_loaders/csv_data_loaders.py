from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .._typing import FilePath

import pandas as pd

from .utils import convert_string_to_int_list, dispatch_to_appropriate_loader

from ..beds_data import BedsData
from ..crop_calendar import CropCalendar
from ..crops_data import CropsData
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


class CSVCropsDataLoader(CSVDataLoader):
    data_cls = CropsData

    @staticmethod
    def _load_v0_0_1(filenames: Sequence[FilePath]) -> tuple[pd.DataFrame, pd.DataFrame]:
        metadata_filename, interactions_filename = filenames
        df_metadata = pd.read_csv(
            metadata_filename,
            sep=";",
            index_col="culture",
            comment="#",
        )
        df_metadata.rename(
            columns={
                "culture": "crop_name",
                "famille": "crop_family",
                "delai_retour": "return_delay",
            },
            inplace=True,
        )

        # TODO fix the data instead
        df_metadata["return_delay"] = df_metadata["return_delay"] * N_WEEKS_PER_YEAR

        df_interactions = pd.read_csv(
            interactions_filename,
            sep=";",
            index_col="culture",
            comment="#",
        )
        df_interactions.rename(
            columns={
                "culture": "crop_name",
            },
            inplace=True,
        )

        return (df_metadata, df_interactions)

    @staticmethod
    def _load_v0_0_2(filenames: Sequence[FilePath]) -> tuple[pd.DataFrame, pd.DataFrame]:
        metadata_filename, interactions_filename = filenames
        df_metadata = pd.read_csv(
            metadata_filename,
            sep=";",
            index_col="crop_name",
            comment="#",
        )

        # TODO fix the data instead
        df_metadata["return_delay"] = df_metadata["return_delay"] * N_WEEKS_PER_YEAR

        df_interactions = pd.read_csv(
            interactions_filename,
            sep=";",
            index_col=0,
            comment="#",
        )

        return (df_metadata, df_interactions)


class CSVCropTypesAttributesLoader(CSVDataLoader):
    @staticmethod
    def _load_v0_1(filename: FilePath) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
        )
        return df
