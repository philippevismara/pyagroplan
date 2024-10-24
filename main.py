import argparse

import constraints as cstrs
from beds_data import BedsDataLoader
from crops_calendar import CropsCalendarLoader
from crops_data import CropsDataLoader
from model import AgroEcoPlanModel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agroecological crops allocation problem solver",
    )
    parser.add_argument(
        "beds_data_path",
        type=str,
        help="path to beds data CSV file"
    )
    parser.add_argument(
        "crops_calendar_path",
        type=str,
        help="path to crops calendar CSV file",
    )
    parser.add_argument(
        "output_path",
        type=str,
        help="path to solution CSV file",
    )
    parser.add_argument(
        "--crops_metadata_path",
        type=str,
        help="path to crops metadata CSV file",
    )
    parser.add_argument(
        "--crops_interactions_path",
        type=str,
        help="path to crops interactions CSV file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
    )

    args = parser.parse_args()
    verbose = args.verbose

    crops_data = None
    if args.crops_metadata_path and args.crops_interactions_path:
        crops_data = CropsDataLoader.load(args.crops_metadata_path, args.crops_interactions_path)

    crops_calendar = CropsCalendarLoader.load(args.crops_calendar_path, crops_data)
    beds_data = BedsDataLoader.load(args.beds_data_path)

    constraints = [
        cstrs.CropsRotationConstraint(crops_calendar),
        # cstrs.DiluteSpeciesConstraint(crops_calendar, beds_data),
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

    solution.to_csv(args.output_path)
