from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

import pandas as pd


class CropsData:
    def __init__(self, df_crops_metadata: pd.DataFrame, df_crops_interactions: pd.DataFrame):
        self.df_metadata = df_crops_metadata.copy()
        self.df_interactions = df_crops_interactions.copy()

        self.n_crops = len(self.df_metadata)

        def crops_interactions(crop_i: str, crop_j: str) -> Any:
            return self.df_interactions.loc[crop_i, crop_j]
        self.crops_interactions = crops_interactions

    def __str__(self) -> str:
        return """CropsData(n_crops={})""".format(self.n_crops)

    def __len__(self) -> int:
        return self.n_crops
