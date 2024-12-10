from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Sequence

import warnings


def convert_string_to_int_list(s: str) -> tuple[int,...]:
    """Converts a string containing a list of ints to a proper tuple of ints.

    Parameters
    ----------
    s : str
        String to convert.

    Returns
    -------
    tuple of int
        Tuple containing the ints from the input string.
    """
    if isinstance(s, float):
        s = str(s)
        if s == "nan":
            return []

    str_list = s.split(",")

    if len(str_list) == 0 or len(str_list[0]) == 0:
        return tuple()
    else:
        return tuple(map(int, str_list))


def read_csv_metadata(filename: str, comment: str="#") -> dict[str, str]:
    """Reads the metadata header from a CSV file.

    Parameters
    ----------
    filename : str
        CSV file to process.
    comment : str, default="#"
        Prefix of the lines containing the metadata.

    Returns
    -------
    dict[str, str]
        Dictionnary mapping the metadata keys to their values.
    """
    metadata = {}

    with open(filename) as fp:
        for row in fp:
            row = row.strip()
            if row[0] != comment:
                break

            row = row[1:].strip()

            key, sep, value = row.partition(":")
            if len(sep) == 0:
                metadata[key.strip()] = "true"
            else:
                metadata[key.strip()] = value.strip()

    return metadata


def dispatch_to_appropriate_loader(filename: str|Sequence[str], scope: object) -> Any:
    """Find the appropriate loader for the given CSV file.

    Reads the file format version in the metadata (from the `format_version` key).
    If the loading fails or no file format version is found, attempts loading with all available loaders.

    Parameters
    ----------
    filename : str
        CSV file to load.
    scope : object
        Object / scope in which to search the loader.

    Returns
    -------
    data : Any

    Warns
    -----
    RuntimeWarning
        If a file format is specified but no explicitly compatible loader can be found.

    Raises
    ------
    RuntimeError
        If no adapted loader can be found.
    """
    try:
        csv_metadata = read_csv_metadata(filename)
    except Exception:
        csv_metadata = read_csv_metadata(filename[0])

    loaded = False

    format_version = csv_metadata.get("format_version", None)
    if format_version:
        func_name = "_load_v" + format_version.replace(".", "_")
        func = getattr(scope, func_name, None)
        if func:
            data = func(filename)
            loaded = True
        else:
            warnings.warn(
                "Specific function for data loading not found, tries using available loaders",
                RuntimeWarning,
            )

    # Attemps to load using all available loaders
    if not loaded:
        func_names = [func_name for func_name in dir(scope) if "_load_v" in func_name]

        for func_name in func_names:
            func = getattr(scope, func_name)
            try:
                data = func(filename)
                loaded = True
                break
            except Exception:
                pass

        if not loaded:
            raise RuntimeError()

    return data
