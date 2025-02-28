from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from collections.abc import Sequence

import pandas as pd

from .utils import convert_string_to_int_list, dispatch_to_appropriate_loader

from ..beds_data import BedsData
from ..crop_calendar import CropCalendar
from ..crops_data import CropsData
from ..past_crop_plan import PastCropPlan

N_WEEKS_PER_YEAR = 52


class CSVDataLoader:
    """
    @classmethod
    def load(cls, filenames: str|Sequence[str], **kwargs) -> Any:
        loaded_data = dispatch_to_appropriate_loader(filenames, cls)
        data = cls.data_cls(loaded_data, **kwargs)
        return data
    """

    ...


class CSVBedsDataLoader(CSVDataLoader):
    data_cls = BedsData

    @staticmethod
    def _load_v0_1(filename: str) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
            header=[0, 1],
        )

        df.loc[:, ("adjacent_beds", slice(None))] = \
            df.loc[:, ("adjacent_beds", slice(None))].map(convert_string_to_int_list)

        return df

    @classmethod
    def load(cls, filename: str) -> BedsData:
        df_beds_data = dispatch_to_appropriate_loader(filename, cls)
        beds_data = cls.data_cls(df_beds_data)
        return beds_data


class CSVPastCropPlanLoader(CSVDataLoader):
    data_cls = PastCropPlan

    @staticmethod
    def _load_v0_1(filename: str) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            converters={
                "allocated_beds_ids": convert_string_to_int_list,
            },
            comment="#",
        )
        return df

    @classmethod
    def load(
        cls, filename: str
    ) -> PastCropPlan:
        df = dispatch_to_appropriate_loader(filename, cls)
        data = cls.data_cls(df)
        return data


class CSVCropCalendarLoader(CSVDataLoader):
    data_cls = CropCalendar

    @staticmethod
    def _load_v0_1(filename: str) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
        )
        return df

    @classmethod
    def load(
        cls,
        filename: str,
        crops_data: Optional[CropsData] = None,
        past_crop_plan: Optional[PastCropPlan] = None,
    ) -> CropCalendar:
        df_crops_calendar = dispatch_to_appropriate_loader(filename, cls)
        crops_calendar = cls.data_cls(df_crops_calendar, crops_data, past_crop_plan)
        return crops_calendar


class CSVCropsDataLoader(CSVDataLoader):
    data_cls = CropsData

    @staticmethod
    def _load_v0_0_1(filenames: Sequence[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
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
    def _load_v0_0_2(filenames: Sequence[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    @classmethod
    def load(cls, metadata_filename: str, interactions_filename: str) -> CropsData:
        df_metadata, df_interactions = dispatch_to_appropriate_loader(
            (metadata_filename, interactions_filename),
            cls,
        )
        crops_data = cls.data_cls(df_metadata, df_interactions)
        return crops_data
