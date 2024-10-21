import argparse

import constraints as cstrs
from beds_data import BedsDataLoader
from crops_calendar import CropsCalendarLoader
from model import AgroEcoPlanModel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agroecological crops allocation problem solver",
    )

    args = parser.parse_args()

    crop_calendar_filename = "data/crops_calendar_1an_v7.csv"
    beds_data_filename = "data/beds_data.csv"
    verbose = True

    crops_calendar = CropsCalendarLoader.load(crop_calendar_filename)
    beds_data = BedsDataLoader.load(beds_data_filename)

    constraints = [
        cstrs.CropsRotationConstraint(crops_calendar),
        # cstrs.DiluteSpeciesConstraint(),
    ]

    print(crops_calendar)
    print(beds_data)
    print(constraints)

    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose)
    model.init(constraints)
    model.configure_solver()
    print(model)

    solution = model.solve()
    print(solution)
