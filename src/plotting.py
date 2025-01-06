from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

    from .beds_data import BedsData
    from .crops_calendar import CropsCalendar
    from .crops_data import CropsData
    from .solution import Solution


import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib import patches
from matplotlib import pyplot as plt



def plot_crops_calendar(
        crops_calendar: CropsCalendar,
        ax: Optional[plt.Axes]=None,
        colors: Optional[dict]=None
) -> plt.Axes:
    if not ax:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.gca()

    colors = colors or {}

    df_crops_calendar = crops_calendar.df_crops_calendar[["crop_name", "starting_week", "ending_week", "allocated_beds_quantity"]]
    first_week = df_crops_calendar["starting_week"].min()
    n_weeks = df_crops_calendar["ending_week"].max()
    n_crops_total = df_crops_calendar["allocated_beds_quantity"].sum()

    offset = 0.
    for i, vals in df_crops_calendar.iterrows():
        p = patches.Rectangle(
            (vals["starting_week"], offset),
            width=vals["ending_week"]-vals["starting_week"],
            height=vals["allocated_beds_quantity"],
            color=colors.get(vals["crop_name"], None),
            antialiased=False,
            linewidth=0,
        )
        offset += p.get_height()
        ax.add_patch(p)
        ax.text(
            p.get_x() + p.get_width()/2,
            p.get_y() + p.get_height()/2,
            vals["crop_name"],
            horizontalalignment="center",
            verticalalignment="center",
        )

    ax.set_xticks(range(n_weeks+1), minor=True)
    ax.set_xticks(range(0, n_weeks+1, 5), minor=False)

    ax.set_xlim(first_week, n_weeks)
    ax.set_ylim(0, n_crops_total)
    ax.invert_yaxis()

    for label in ax.get_xticklabels()[1:]:
        x, y = label.get_position()
        ax.text(x+0.5, n_crops_total+0.05, label.get_text(), ha="center", va="top")
    ax.set_xticklabels([])

    for label in ax.get_yticklabels()[:n_crops_total]:
        x, y = label.get_position()
        ax.text(0.9, y+0.5, label.get_text(), ha="right", va="center")
    ax.set_yticklabels([])

    ax.grid(axis="x", which="both", ls="--")

    return ax


def plot_beds_adjacency_graph(
        beds_data: BedsData,
        ax: Optional[plt.Axes]=None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure()
        ax = fig.gca()

    beds_adjacency_graph = beds_data.get_adjacency_graph()

    if "garden_id" in beds_data.df_beds_data.columns:
        gb = beds_data.df_beds_data.groupby("garden_id")
        gardens = gb.groups
    else:
        components = nx.connected_components(beds_adjacency_graph)
        gardens = {
            i: nodes
            for i, nodes in enumerate(components)
        }

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


def plot_interactions_graph(
        crops_data: CropsData,
        ax: Optional[plt.Axes]=None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure()
        ax = fig.gca()

    interactions_graph = crops_data.get_interactions_graph()
    nx.draw_networkx(
        interactions_graph,
        nx.circular_layout(interactions_graph),
        ax=ax,
        with_labels=True,
        edge_color=list(e[-1] for e in interactions_graph.edges.data("weight")),
        edge_cmap=colormaps["RdYlGn"],
        edge_vmin=-1,
        edge_vmax=1,
        width=4,
    )
    ax.axis("off")

    return ax


def plot_solution(
        solution: Solution,
        beds_data: BedsData,
        colors: Optional[dict]=None,
        ax: Optional[plt.Axes]=None,
) -> plt.Axes:
    if not ax:
        fig = plt.figure(figsize=(5, 5))
        ax = fig.gca()

    from collections import defaultdict
    colors = colors if colors is not None else defaultdict()

    beds_adjacency_graph = beds_data.get_adjacency_graph()
    plots_data = [(list(cc)[0], len(cc)) for cc in nx.connected_components(beds_adjacency_graph)]
    plots, sizes = list(zip(*plots_data))

    df_solution = solution.crops_planning
    first_week = df_solution["starting_week"].min()
    n_weeks = df_solution["ending_week"].max()
    n_beds = sum(sizes)

    for i, vals in df_solution.iterrows():
        p = patches.Rectangle(
            (vals["starting_week"], vals["assignment"]),
            width=vals["ending_week"]-vals["starting_week"],
            height=1,
            color=colors[vals["crop_name"]],
            antialiased=False,
            linewidth=0,
        )
        ax.add_patch(p)
        ax.text(
            p.get_x() + p.get_width()/2,
            p.get_y() + p.get_height()/2,
            vals["crop_name"],
            horizontalalignment="center",
            verticalalignment="center",
        )

    ax.hlines(y=np.cumsum(sizes)[:-1]+1, xmin=0, xmax=n_weeks, lw=3)

    ax.set_xticks(range(n_weeks+1), minor=True)
    ax.set_xticks(range(0, n_weeks+1, 5), minor=False)

    for label in ax.get_xticklabels()[1:]:
        x, y = label.get_position()
        ax.text(x+0.5, n_beds+1.05, label.get_text(), ha="center", va="top")
    ax.set_xticklabels([])

    for label in ax.get_yticklabels()[1:n_beds+1]:
        x, y = label.get_position()
        ax.text(0.9, y+0.5, label.get_text(), ha="right", va="center")
    ax.set_yticklabels([])

    ax.set_xlim(first_week, n_weeks)
    ax.set_ylim(1, n_beds+1)
    ax.invert_yaxis()

    ax.grid(axis="x", which="both", ls="--")

    return ax
