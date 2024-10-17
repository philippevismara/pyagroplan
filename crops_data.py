import pandas as pd


class CropsDataLoader:
    @staticmethod
    def load(metadata_filename, interactions_filename):
        df_metadata = pd.read_csv(
            metadata_filename,
            sep=";",
            index_col="culture",
        )
        df_interactions = pd.read_csv(
            interactions_filename,
            sep=";",
            index_col="culture",
        )
        return CropsData(df_metadata, df_interactions)


class CropsData:
    def __init__(self, df_crops_metadata, df_crops_interactions):
        self.df_metadata = df_crops_metadata.copy()
        self.df_interactions = df_crops_interactions.copy()

        self.n_crops = len(self.df_metadata)

        def crops_interactions(crop_i, crop_j):
            return self.df_interactions.loc[crop_i, crop_j]
        self.crops_interactions = crops_interactions

    def __str__(self):
        return """CropsData(n_crops={})""".format(self.n_crops)

    def __len__(self):
        return self.n_crops
