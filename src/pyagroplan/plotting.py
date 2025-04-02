from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Any, Optional

    from .beds_data import BedsData
    from .crop_calendar import CropCalendar
    from .solution import Solution

import datetime
from itertools import cycle

import networkx as nx
import numpy as np
from matplotlib import colormaps
from matplotlib import patches
from matplotlib import pyplot as plt


def get_crops_colors_by_botanical_family(
    crop_calendar: CropCalendar,
    colors_list: Optional[Collection] = None,
) -> dict[str, Any]:
    if colors_list is None:
        from matplotlib import colormaps
        colors_list = colormaps["tab20"].colors

    families_names = crop_calendar.df_crop_calendar["botanical_family"].unique()
    families_names.sort()

    fam_colors = {
        family_name: color
        for family_name, color in zip(families_names, cycle(colors_list))
    }

    crops_data = crop_calendar.df_crop_calendar.drop_duplicates(
        subset=["crop_name", "botanical_family"]
    )

    crops_colors = {
        crop_data.crop_name: fam_colors[crop_data.botanical_family]
        for crop_data in crops_data.itertuples()
    }

    return crops_colors


def plot_crop_calendar(
    crop_calendar: CropCalendar,
    ax: Optional[plt.Axes] = None,
    colors: Optional[dict | str] = "auto",
) -> plt.Axes:
    if not ax:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.gca()

    colors = colors or {}
    if colors == "auto":
        colors = get_crops_colors_by_botanical_family(crop_calendar)

    df_crop_calendar = crop_calendar.df_crop_calendar[
        ["crop_name", "starting_date", "ending_date", "quantity"]
    ]
    first_date = df_crop_calendar["starting_date"].min()
    last_date = df_crop_calendar["ending_date"].max()
    n_days = last_date - first_date
    n_crops_total = df_crop_calendar["quantity"].sum()

    offset = 0.0
    for i, vals in df_crop_calendar.iterrows():
        p = patches.Rectangle(
            (vals["starting_date"], offset),
            width=vals["ending_date"] - vals["starting_date"],
            height=vals["quantity"],
            color=colors.get(vals["crop_name"], None),
            antialiased=False,
            linewidth=0,
        )
        offset += p.get_height()
        ax.add_patch(p)
        ax.text(
            p.get_x() + p.get_width() / 2,
            p.get_y() + p.get_height() / 2,
            vals["crop_name"],
            horizontalalignment="center",
            verticalalignment="center",
        )

    years_list = list(range(first_date.year, last_date.year+1))
    ax.set_xticks(
        [datetime.date(year, 1, 1) for year in years_list],
        labels=years_list,
        minor=False,
    )
    year, week, _ = first_date.isocalendar()
    first_week = datetime.date.fromisocalendar(year, week, 1)
    year, week, _ = last_date.isocalendar()
    last_week = datetime.date.fromisocalendar(year, week, 7)
    weeks_list = np.arange(first_week, last_week, 7)
    ax.set_xticks(
        weeks_list,
        minor=True,
    )

    ax.set_xlim(first_date, last_date)
    ax.set_ylim(0, n_crops_total)
    ax.invert_yaxis()

    ax.grid(axis="x", which="major", ls="-", color="black")
    ax.grid(axis="x", which="minor", ls="-", alpha=0.5)
    ax.set_axisbelow(True)

    return ax


def plot_beds_adjacency_graph(
    beds_data: BedsData,
    adjacency_name: str,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure()
        ax = fig.gca()

    beds_adjacency_graph = beds_data.get_adjacency_graph(adjacency_name)

    if "garden_id" in beds_data.df_beds_data.columns:
        gb = beds_data.df_beds_data.groupby("garden_id")
        gardens = gb.groups
    else:
        components = nx.connected_components(beds_adjacency_graph)
        gardens = {i: nodes for i, nodes in enumerate(components)}

    layout = nx.multipartite_layout(
        beds_adjacency_graph,
        subset_key=gardens,
        align="horizontal",
    )

    nx.draw_networkx(
        beds_adjacency_graph,
        layout,
        node_color="gray",
        ax=ax,
    )
    ax.axis("off")

    return ax


def plot_solution(
    solution: Solution,
    beds_data: BedsData,
    colors: Optional[dict | str] = "auto",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.gca()

    from collections import defaultdict

    colors = colors if colors is not None else defaultdict()
    if colors == "auto":
        colors = get_crops_colors_by_botanical_family(solution.crop_calendar)

    sizes = beds_data.df_beds_data["metadata"]["garden"].value_counts(sort=False).values

    df_solution = solution.crops_planning
    first_date = df_solution["starting_date"].min()
    last_date = df_solution["ending_date"].max()
    n_beds = beds_data.n_beds

    for i, vals in df_solution.iterrows():
        p = patches.Rectangle(
            (vals["starting_date"], vals["assignment"]),
            width=vals["ending_date"] - vals["starting_date"],
            height=1,
            color=colors[vals["crop_name"]],
            antialiased=False,
            linewidth=0,
        )
        ax.add_patch(p)
        ax.text(
            p.get_x() + p.get_width() / 2,
            p.get_y() + p.get_height() / 2,
            vals["crop_name"],
            horizontalalignment="center",
            verticalalignment="center",
        )

    # Shows years on horizontal axis
    years_list = list(range(first_date.year, last_date.year+1))
    ax.set_xticks(
        [datetime.date(year, 1, 1) for year in years_list],
        labels=years_list,
        minor=False,
    )
    year, week, _ = first_date.isocalendar()
    first_week = datetime.date.fromisocalendar(year, week, 1)
    year, week, _ = last_date.isocalendar()
    last_week = datetime.date.fromisocalendar(year, week, 7)
    weeks_list = np.arange(first_week, last_week, 7)
    ax.set_xticks(
        weeks_list,
        minor=True,
    )

    ax.set_xlim(first_date, last_date)
    ax.grid(axis="x", which="major", ls="-", color="black")
    ax.grid(axis="x", which="minor", ls="-", alpha=0.5)
    ax.set_axisbelow(True)

    # Shows gardens on vertical axis
    gardens_limits = np.cumsum([0] + list(sizes))
    ax.hlines(
        y=gardens_limits[1:-1],
        xmin=first_date,
        xmax=last_date,
        lw=3,
        colors="black",
    )
    garden_names = beds_data.df_beds_data["metadata"]["garden"].unique()
    for i, garden_name in enumerate(garden_names):
        ax.text(
            first_date,
            gardens_limits[i:i+2].mean(),
            "garden " + garden_name,
            horizontalalignment="center",
            verticalalignment="center",
            rotation=90,
        )
    ax.set_yticks([])
    ax.set_ylim(0, n_beds)
    ax.invert_yaxis()

    return ax
