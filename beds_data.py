import pandas as pd


class BedsDataLoader:
    @staticmethod
    def load(filename):
        df = pd.read_csv(filename, sep=";")
        df_beds_data = df[["planche", "planche_contact"]]
        beds_data = BedsData(df_beds_data)
        return beds_data


class BedsData:
    def __init__(self, df_beds_data):
        self.df_beds_data = df_beds_data

        def adjacency_function(i, j):
            return j in df_beds_data["planche_contact"].loc[i]
        self.adjacency_function = adjacency_function

        self.n_beds = len(self.df_beds_data)

    def __str__(self):
        return """BedsData(n_beds={})""".format(self.n_beds)
