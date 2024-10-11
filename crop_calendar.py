import networkx as nx
import numpy as np
import pandas as pd


class CropCalendarLoader:
    @staticmethod
    def load(filename):
        df = pd.read_csv(filename, sep=";")
        df_crop_calendar = df[["culture", "debut", "fin", "quantite"]]
        crop_calendar = CropCalendar(df_crop_calendar)
        return crop_calendar


class CropCalendar:
    def __init__(self, df_crop_calendar):
        self.df_crop_calendar = df_crop_calendar.copy()

        df = self.df_crop_calendar
        repeats = df["quantite"].values
        self.crops_groups = np.repeat(df.index.values, repeats)
        df = df.loc[self.crops_groups]
        self.crops_groups_assignments = np.split(np.arange(len(df)), np.cumsum(repeats)[:-1])
        df.drop(columns="quantite", inplace=True)
        self.crop_calendar = df[["culture", "debut", "fin"]].values

        self.n_assignments = len(self.crop_calendar)

        from interval_graph import interval_graph
        self._interval_graph = interval_graph(list(map(list, self.crop_calendar[:,1:].astype(int))))
        self.overlapping_assignments = frozenset(
            frozenset(node[0] for node in clique)
            for clique in nx.chordal_graph_cliques(self._interval_graph)
        )

    def __str__(self):
        return """CropCalendar(n_crops={}, n_assignments={})""".format(len(self.df_crop_calendar), self.n_assignments)
