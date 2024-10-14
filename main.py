import argparse

import constraints
from beds_data import BedsDataLoader
from crop_calendar import CropCalendarLoader
from model import AgroEcoPlanModel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agroecological crop allocation problem solver",
    )

    args = parser.parse_args()

    crop_calendar_filename = "data/crop_calendar_1an_v7.csv"
    beds_data_filename = "data/beds_data.csv"
    verbose = True

    crop_calendar = CropCalendarLoader.load(crop_calendar_filename)
    beds_data = BedsDataLoader.load(beds_data_filename)

    constraints = [
        constraints.CropRotationConstraint(),
        # constraints.DiluteSpeciesConstraint(),
    ]

    print(crop_calendar)
    print(beds_data)
    print(constraints)

    model = AgroEcoPlanModel(crop_calendar, beds_data, verbose)
    model.init(constraints)
    model.configure_solver()
    print(model)

    solution = model.solve()
    print(solution)
