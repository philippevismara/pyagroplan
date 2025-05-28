# Pyagroplan

[![python-package](https://github.com/philippevismara/pyagroplan/actions/workflows/python-package.yml/badge.svg)](https://github.com/philippevismara/pyagroplan/actions)
[![code-style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

The software has been tested for Python versions >= 3.10.
The package and its dependencies can be installed using `pip`:
```script
pip install .
```


## Unit tests

To run unit tests, from the root directory, execute:
```script
python -m pytest tests
```


## Documentation

To build the documentation, first make sure to have the dependencies installed:
```script
pip install -r docs/docs_requirements.txt
```

Then, execute:
```script
cd docs
make html
```

The documentation is then available at `docs/build/html/index.html`.


## Data format

There 4 main data files respectively containing:
- the beds data
- the future crop calendar
- the past crop plan (optional)
- crop type attributes

Each of these data files are semicolon-separated CSV files.
They can contain a header with lines starting by a hash `#`, each line being of the form of a key-value pair.
Here is a typical example:
```
# description: My data file
# data_version: 1.0
# format_version: 0.1
```
It consists of 3 fields:
- `description` providing a textual description of the data
- `data_version` providing a version number of the data (for instance in case the data is updated during a workshop)
- `format_version` providing the version of the data format (to allow the data format thoughout with different versions of `pyagroplan`)


### Beds data

This file contains the data describing the farm layout and its design.
It consists in X columns:
- `bed_id` (integer): identifier of the bed
- `garden` (string): name of the garden in which is located the bed
- `geolocalised_shape` (optional, WKT string): contains the polygon geolocalised using WGS84 (GPS) coordinates, useful for plotting the gardens and beds

It also contains the user-defined adjacency measures as comma-separated adjacency lists (e.g., `1` or `0,2`).

It can also contain other user-defined attributes (e.g., `orientation`, `position_in_garden`, `is_in_shade_during_summer`, etc.).


### Future crop calendar

This file contains the crop calendar to be allocated to beds.
It consists in 5 columns:
- `crop_name` (string): name of the crop (e.g., `Cauliflower`)
- `crop_type` (string): type of the crop (e.g., `cabbage`), each crop is associated to a unique crop type regrouping crops having similar properties
- `starting_date` (date): starting date (included) when the crop is cultivated (i.e., when the bed is totally allocated to this crop)
- `ending_date` (date): idem but for the ending date (included)
- `quantity` (integer): number of beds to allocate to this crop

There are two format to specify the dates:
- using ISO8601 calendar dates format, i.e., dates of the form `YYYY-MM-DD` (e.g., `2023-11-03`)
- using ISO8601 week dates format, i.e., dates of the form `YYYY-Www` (e.g., `2023-W45`)


### Past crop plan (optional)

This file contains the crop plan used during the previous years.
It is thus optional as in some cases we might not have that data (e.g., when working in a newly designed farm) or might not want to use it.
It is very similar to the crop calendar data format and consists in 5 columns:
- `crop_name` (string): name of the crop (e.g., `Cauliflower`)
- `crop_type` (string): type of the crop (e.g., `cabbage`), each crop is associated to a unique crop type regrouping crops having similar properties
- `starting_date` (date): 
- `ending_date` (date): date when the crop is (inclusive)
- `allocated_beds_ids` (list of integers): comma-separated list of beds allocated to this crop (e.g., `50` or `70,71`)

The dates follow the same format than in the crop calendar:
- using ISO8601 calendar dates format, i.e., dates of the form `YYYY-MM-DD` (e.g., `2023-11-03`)
- using ISO8601 week dates format, i.e., dates of the form `YYYY-Www` (e.g., `2023-W45`)


### Crop type attributes

This file contains the properties of each crop type being used in the model.
The first column is thus the `crop_type` and all the other ones contain its property.
It is thus entirely up to the user to decide what knowledge they wants to incorporate in their model.
Here are some examples of possible columns one might want to use: `botanical_family`, `weedy_soil_sensitivity`, `requires_shade_in_summer`, etc.


## Format of the constraint definition dictionary

To simplify the use of this package, it is possible to completely configure the constraints using a dictionary.
It contains an entry for each constraint.
Here is an example:

```python
constraints_definitions = {
    "crops_requiring_shade_in_summer": {
        "constraint_type": "compatible_beds_constraint",
        "type": "enforced",
        "crops_selection_rule": """crop["requires_shade_in_summer"] & (crop["cultivation_season"] != "winter")""",
        "beds_selection_rule": """bed["is_in_shade_during_summer"]""",
    },
    "return_delays": {
        "constraint_type": "return_delays_constraint",
        "return_delays": "data/return_delays.csv",
    },
    "forbid_favouring_weed_crop_before_weed-free_requirering_crop": {
        "constraint_type": "precedence_constraint",
        "type": "forbidden",
        "precedence_effect_delay_in_weeks": "6",
        "rule": """(preceding_crop["effect_on_weeds"] == "favouring") & (following_crop["weedy_soil_sensitivity"] == "high")""",
    },
    "forbid_cucurbitaceae_on_adjacent_beds": {
        "constraint_type": "spatial_interactions_constraint",
        "type": "forbidden",
        "adjacency_type": "adjacent_beds_in_garden",
        "rule": """(crop1["botanical_family"] == "cucurbitaceae") & (crop2["botanical_family"] == "cucurbitaceae")""",
    },
    "group_crops": {
        "constraint_type": "group_crops_constraint",
        "adjacency_type": "adjacent_beds_in_garden",
        "group_by": "crop_group_id",
    },
}
```

Each individual constraint is defined using a dictionary.
The type of the constraint is specified using the field `constraint_type` which takes a value among `compatible_beds_constraint`, `return_delays_constraint`, `precedence_constraint`, `spatial_interactions_constraint`, `group_crops_constraint`.

Each constraint has its own set of parameters which are always given as a string.

Note that, behind the scene, the "rule" parameters are actually evaluated using Python's `eval()` operated on `pandas` `Dataframe`.
In particular, this is why the classic operators follows `pandas` syntax and not Python's one:
- `&` is the `and` operator
- `|` is the `or` operator
- `~` is the `not` operator

### Compatible beds constraint (`compatible_beds_constraint`)

- `type`: `enforced` or `forbidden`
- `crops_selection_rule`: boolean expression selecting on which `crop` this constraint is applied
- `beds_selection_rule`: boolean expression selecting which `bed` are allowed or disallowed

### Return delays constraint (`return_delays_constraint`)

- `return_delays`: path to the CSV file containing the return delays matrix

### Precedence constraint (`precedence_constraint`)

- `type`: `enforced` or `forbidden`
- `precedence_effect_delay_in_weeks`: integer specifying how long in weeks the precedence effect is effective
- `rule`: boolean expression selecting which pairs of crops it is applied on (through `preceding_crop` and `following_crop`)

### Spatial interactions constraint (`spatial_interactions_constraint`)

- `type`: `enforced` or `forbidden`
- `adjacency_type`: name of one of the adjacency measure defined in the beds data to use
- `intervals_overlap` (optional): restricts the constraint to specific overlaps of the cultivation intervals (default: `[1,-1][1,-1]`)
- `rule`: boolean expression selecting which pairs of crops it is applied on (through `crop1` and `crop2`, note that this constraint is symmetric)

### Group crops constraint (`group_crops_constraint`)

- `adjacency_type`: name of one of the adjacency measure defined in the beds data to use
- `group_by`: name of the field to perform the group by on (typically `crop_group_id`)
- `filtering_rule`: boolean expression selecting which crops it is applied on (through `crop`)


## License

Pyagroplan has a CeCILL-C license, as found in the [LICENSE.md](LICENSE.md) file.
