import pandas as pd


class CropsDataLoader:
    @staticmethod
    def load(filename):
        df = pd.read_csv(
            filename,
            sep=";",
            index_col="culture",
        )
        return CropsData(df)


class CropsData:
    def __init__(self, df_crops_data):
        self.df_crops_data = df_crops_data.copy()

        self.n_crops = len(df_crops_data)

        def crops_interactions(crop_i, crop_j):
            return self.df_crops_data.loc[crop_i, crop_j]
        self.crops_interactions = crops_interactions

    def __str__(self):
        return """CropsData(n_crops={})""".format(self.n_crops)

    def __len__(self):
        return self.n_crops
