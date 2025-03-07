from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    import networkx as nx

import pandas as pd

from ._typing import FilePath


class CropsData:
    """Handles crops data.

    Attributes
    ----------
    df_metadata : pd.DataFrame
        DataFrame containing the raw metadata of crops.
    df_interactions : pd.DataFrame
        DataFrame containing the raw interactions matrix.
    n_crops : int
        Number of different types of crops defined.
    crops_interactions : Callable[[str, str], Any]
        Function returning the interaction between two crops.

    Parameters
    ----------
    df_crops_metadata : pd.DataFrame
        DataFrame containing the raw metadata of crops.
    df_crops_interactions : pd.DataFrame
        DataFrame containing the raw interactions matrix.
    """

    def __init__(
        self,
        df_crops_metadata: pd.DataFrame | FilePath,
        df_crops_interactions: pd.DataFrame | FilePath,
    ):
        if isinstance(df_crops_metadata, FilePath):
            from .data_loaders import CSVCropsDataLoader
            df_crops_metadata, df_crops_interactions = CSVCropsDataLoader.load((
                df_crops_metadata,
                df_crops_interactions,
            ))
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

    def get_interactions_graph(self) -> nx.Graph:
        """Builds the interactions graph between crops.

        Returns
        -------
        nx.Graph
        """
        import networkx as nx
        return nx.from_pandas_adjacency(self.df_interactions)
