from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional
    from collections.abc import Sequence

import pandas as pd

from .utils import dispatch_to_appropriate_loader

from ..beds_data import BedsData
from ..crops_calendar import CropsCalendar
from ..crops_data import CropsData

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
    def _load_v0_0_1(filename: str) -> pd.DataFrame:
        def list_converter(s: str) -> tuple[int,...]:
            str_list = s.split(",")

            if len(str_list) == 0 or len(str_list[0]) == 0:
                return tuple()
            else:
                return tuple(map(int, str_list))

        df_beds_data = pd.read_csv(
            filename,
            sep=";",
            converters={
                "planche_contact": list_converter
            },
            index_col="planche",
            comment="#",
        )
        df_beds_data.rename(columns={
            "planche": "bed_id",
            "planche_contact": "adjacent_beds_ids",
            "jardin": "garden_id",
        }, inplace=True)
        return df_beds_data

    @classmethod
    def load(cls, filename: str) -> BedsData:
        df_beds_data = dispatch_to_appropriate_loader(filename, cls)
        beds_data = cls.data_cls(df_beds_data)
        return beds_data


class CSVCropsCalendarLoader(CSVDataLoader):
    data_cls = CropsCalendar

    @staticmethod
    def _load_v0_0_1(filename: str) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
        )
        df_crops_calendar = df[["culture", "debut", "fin", "quantite"]].copy()

        # TODO fix the data instead
        df_crops_calendar["culture"] = df_crops_calendar["culture"].str.lower()
        df_crops_calendar["culture"] = df_crops_calendar["culture"].str.replace(" ", "_")

        df_crops_calendar.rename(columns={
            "culture": "crop_name",
            "debut": "starting_week",
            "fin": "ending_week",
            "quantite": "allocated_beds_quantity",
        }, inplace=True)

        return df_crops_calendar

    @staticmethod
    def _load_v0_0_2(filename: str) -> pd.DataFrame:
        df = pd.read_csv(
            filename,
            sep=";",
            comment="#",
        )
        df_crops_calendar = df[[
            "crop_name",
            "starting_week",
            "ending_week",
            "allocated_beds_quantity"
        ]]
        return df_crops_calendar

    @classmethod
    def load(cls, filename: str, crops_data: Optional[CropsData]=None) -> CropsCalendar:
        df_crops_calendar = dispatch_to_appropriate_loader(filename, cls)
        crops_calendar = cls.data_cls(df_crops_calendar, crops_data)
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
        df_metadata.rename(columns={
            "culture": "crop_name",
            "famille": "crop_family",
            "delai_retour": "return_delay",
        }, inplace=True)

        # TODO fix the data instead
        df_metadata["return_delay"] = df_metadata["return_delay"] * N_WEEKS_PER_YEAR

        df_interactions = pd.read_csv(
            interactions_filename,
            sep=";",
            index_col="culture",
            comment="#",
        )
        df_interactions.rename(columns={
            "culture": "crop_name",
        }, inplace=True)

        return (df_metadata, df_interactions)

    @classmethod
    def load(cls, metadata_filename: str, interactions_filename: str) -> CropsData:
        df_metadata, df_interactions = dispatch_to_appropriate_loader((metadata_filename, interactions_filename), cls)
        crops_data = cls.data_cls(df_metadata, df_interactions)
        return crops_data
