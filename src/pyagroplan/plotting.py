from __future__ import annotations

"""
Module for visualizing crop calendars, beds, and crop planning solutions.

This module provides functions to create visualizations for agricultural planning,
including crop calendar timelines, bed layouts, adjacency graphs, and crop allocation plans.

Functions:
    get_crops_colors_by_botanical_family: Maps crop names to colors based on botanical families.
    plot_crop_calendar: Visualizes a crop calendar as a timeline.
    plot_beds: Displays beds on a geographic map with optional attribute coloring.
    plot_beds_adjacency_graph: Draws a network graph of bed adjacencies.
    plot_crop_plan: Visualizes crop allocations across beds over time.
    plot_solution: Plots a complete crop planning solution.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Any, Optional

    import pandas as pd

    from .data import BedsData, CropCalendar
    from .solution import Solution

import datetime
from itertools import cycle

import networkx as nx
import numpy as np
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
    future_crop_calendar_only: bool = True,
) -> plt.Axes:
    if not ax:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.gca()

    colors = colors or {}
    if colors == "auto":
        colors = get_crops_colors_by_botanical_family(crop_calendar)

    if future_crop_calendar_only:
        df_crop_calendar = crop_calendar.df_future_crop_calendar
    else:
        df_crop_calendar = crop_calendar.df_crop_calendar

    df_crop_calendar = df_crop_calendar[
        ["crop_name", "starting_date", "ending_date", "quantity"]
    ]
    first_date = df_crop_calendar["starting_date"].min()
    last_date = df_crop_calendar["ending_date"].max()
    n_crops_total = len(df_crop_calendar)

    offset = 0.0
    for i, vals in df_crop_calendar.iterrows():
        if vals.quantity == 1:
            text = vals.crop_name
        else:
            text = f"{vals.crop_name} (x{vals.quantity})"

        p = patches.Rectangle(
            (vals["starting_date"], offset),
            width=vals["ending_date"] - vals["starting_date"],
            height=1,
            color=colors.get(vals["crop_name"], None),
            antialiased=False,
            linewidth=0,
        )
        offset += p.get_height()
        ax.add_patch(p)
        ax.text(
            p.get_x() + p.get_width() / 2,
            p.get_y() + p.get_height() / 2,
            text,
            horizontalalignment="center",
            verticalalignment="center",
        )

    years_list = list(range(first_date.year, last_date.year + 1))
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
    ax.get_yaxis().set_visible(False)

    ax.grid(axis="x", which="major", ls="-", color="black")
    ax.grid(axis="x", which="minor", ls="-", alpha=0.5)
    ax.set_axisbelow(True)

    return ax


def plot_beds(
    beds_data: BedsData,
    color_attribute: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure()
        ax = fig.gca()

    df_beds = beds_data.df_beds_data
    crs_wgs84 = "EPSG:4326"

    import geopandas as gpd
    import shapely

    gdf_beds = gpd.GeoDataFrame(
        df_beds, geometry=shapely.from_wkt(df_beds["geolocalised_shape"]), crs=crs_wgs84
    )

    gdf_gardens = gdf_beds.groupby("garden").geometry.apply(
        lambda s: shapely.convex_hull(s.union_all())
    )
    gdf_gardens = gdf_gardens.set_crs(crs_wgs84)

    gdf_gardens.plot(color="sandybrown", ax=ax, zorder=-1)

    centers = shapely.centroid(gdf_gardens)
    for garden_name, center in zip(centers.index, centers):
        ax.text(
            center.x,
            center.y,
            garden_name,
            ha="center",
            va="center",
            bbox={
                "lw": 0,
                "facecolor": "white",
                "alpha": 0.95,
            },
        )

    if color_attribute:
        if color_attribute not in gdf_beds:
            raise ValueError(f"{color_attribute} is not an attribute of beds data")

        pos_beds = gdf_beds[gdf_beds[color_attribute]]
        pos_beds.plot(color="green", ax=ax, zorder=-1)
        pos_patch = patches.Patch(color="green", label="True")

        neg_beds = gdf_beds[~gdf_beds[color_attribute]]
        neg_beds.plot(color="red", ax=ax, zorder=-1)
        neg_patch = patches.Patch(color="red", label="False")

        ax.legend(handles=[pos_patch, neg_patch])
    else:
        gdf_beds.plot(color="green", ax=ax, zorder=-1)

    return ax


def plot_beds_adjacency_graph(
    beds_data: BedsData,
    adjacency_column_name: str,
    ax: Optional[plt.Axes] = None,
    colouring_column_name: Optional[str] = None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure()
        ax = fig.gca()

    beds_adjacency_graph = beds_data.get_adjacency_graph(adjacency_column_name)

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

    if colouring_column_name is not None:
        # build the list of colors for each bed according to the different values of the colouring columnn
        if colouring_column_name not in beds_data.df_beds_data.columns:
            raise ValueError(
                f"{colouring_column_name} is not an attribute of beds data"
            )
        values = beds_data.df_beds_data[colouring_column_name].unique().tolist()
        if len(values) <= 10:
            color_list = plt.cm.tab10.colors[: len(values)]
        else:
            color_list = plt.cm.tab20.colors[: len(values)]
        colors = [
            color_list[values.index(val) % len(color_list)]
            for val in beds_data.df_beds_data[colouring_column_name]
        ]
    else:
        colors = "gray"

    nx.draw_networkx(
        beds_adjacency_graph,
        layout,
        node_color=colors,
        ax=ax,
    )
    ax.axis("off")

    return ax


def plot_crop_plan(
    beds_data: BedsData,
    crop_calendar: CropCalendar,
    df_crop_plan: Optional[pd.DataFrame] = None,
    colors: Optional[dict | str] = "auto",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.gca()

    if df_crop_plan is None:
        if hasattr(crop_calendar, "past_crop_plan"):
            past_crop_plan = crop_calendar.past_crop_plan
            df_crop_plan = past_crop_plan.df_past_assignments.copy()
            df_crop_plan["allocated_bed_id"] = past_crop_plan.allocated_bed_id
        else:
            raise ValueError(
                "df_crop_plan not set but no past crop plan found in crop_calendar"
            )

    from collections import defaultdict

    colors = colors if colors is not None else defaultdict()
    if colors == "auto":
        colors = get_crops_colors_by_botanical_family(crop_calendar)

    sizes = beds_data.df_beds_data["garden"].value_counts(sort=False).values

    first_date = df_crop_plan["starting_date"].min()
    last_date = df_crop_plan["ending_date"].max()
    n_beds = beds_data.n_beds

    for i, vals in df_crop_plan.iterrows():
        p = patches.Rectangle(
            (vals["starting_date"], vals["allocated_bed_id"]),
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
    years_list = list(range(first_date.year, last_date.year + 1))
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
    garden_names = beds_data.df_beds_data["garden"].unique()
    for i, garden_name in enumerate(garden_names):
        ax.text(
            first_date,
            gardens_limits[i : i + 2].mean(),
            "garden " + garden_name,
            horizontalalignment="center",
            verticalalignment="center",
            rotation=90,
        )
    ax.set_yticks([])
    ax.set_ylim(0, n_beds)
    ax.invert_yaxis()

    return ax


def plot_solution(
    solution: Solution,
    colors: Optional[dict | str] = "auto",
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    # TODO normalize name throughout package
    df_crop_plan = solution.crops_planning.rename(
        columns={"assignment": "allocated_bed_id"}
    )

    return plot_crop_plan(
        solution.crop_plan_problem_data.beds_data,
        solution.crop_plan_problem_data.crop_calendar,
        df_crop_plan=df_crop_plan,
        colors=colors,
        ax=ax,
    )
