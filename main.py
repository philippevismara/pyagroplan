import argparse

from src import constraints as cstrs
from src.data_loaders import CSVBedsDataLoader, CSVCropsCalendarLoader, CSVCropsDataLoader
from src.model import AgroEcoPlanModel, available_search_strategies


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
        "--search_strategy",
        type=str,
        choices=available_search_strategies.keys(),
        default="default",
        help="which search strategy to use",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
    )

    args = parser.parse_args()
    search_strategy = args.search_strategy
    verbose = args.verbose

    crops_data = None
    if args.crops_metadata_path and args.crops_interactions_path:
        crops_data = CSVCropsDataLoader.load(args.crops_metadata_path, args.crops_interactions_path)

    crops_calendar = CSVCropsCalendarLoader.load(args.crops_calendar_path, crops_data)
    beds_data = CSVBedsDataLoader.load(args.beds_data_path)

    # Scenario 1
    """
    constraints = [
        cstrs.ForbidNegativeInteractionsConstraint(
            crops_calendar,
            beds_data,
            implementation="distance",
        ),
    ]
    """
    # TODO add objective function

    # Scenario 2
    constraints = [
        cstrs.CropsRotationConstraint(crops_calendar),
        cstrs.DiluteSpeciesConstraint(crops_calendar, beds_data),
    ]

    # Scenario 3
    """
    from src.data_loaders.utils import convert_string_to_int_list
    constraints = [
        cstrs.UnitaryCropsBedsConstraint(
            crops_calendar,
            beds_data,
            beds_selection_func=lambda crop_data, _: convert_string_to_int_list(crop_data["forbidden_beds"]),
            forbidden=True,
        ),
        cstrs.GroupIdenticalCropsTogetherConstraint(crops_calendar, beds_data),
    ]
    """

    print(crops_calendar)
    print(beds_data)
    print(constraints)

    model = AgroEcoPlanModel(crops_calendar, beds_data, verbose)
    model.init(constraints)
    model.configure_solver(search_strategy)
    print(model)

    model.solver.show_short_statistics()
    solution = model.solve()
    print(solution)

    solution.to_csv(args.output_path)
