from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from collections.abc import Sequence

    from pychoco.constraints.cnf.log_op import LogOp
    from pychoco.constraints.constraint import Constraint as ChocoConstraint
    from pychoco.variables.boolvar import BoolVar
    from pychoco.variables.intvar import IntVar

    from ..beds_data import BedsData
    from ..crops_calendar import CropsCalendar
    from ..model import Model
    from ..solution import Solution

from abc import ABC, abstractmethod

import networkx as nx
import pandas as pd


class Constraint(ABC):
    """Abstract class from which all mid-level constraints are derived.

    Child classes must implement the `build` method.
    """

    @abstractmethod
    def build(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint | BoolVar | LogOp]:
        """Abstract method building the constraint.

        Parameters
        ----------
        model : Model
            Model to apply the constraint to.
        assignment_vars : Sequence[IntVar]
            Sequence containing the assignment variables.

        Returns
        -------
        Sequence
            Either a sequence of Pychoco constraints or of BoolVar.
        """
        ...

    @abstractmethod
    def check_solution(self, solution: Solution) -> tuple[bool, list]:
        """Abstract method checking if the provided solution satisfies the constraint.

        Parameters
        ----------
        solution : Solution
            Solution to check.

        Returns
        -------
        bool
            True if the solution satisfies the constraint.
        list
            List of assignments violating the constraint.
        """
        ...


class LocationConstraint(Constraint):
    """Implements unitary constraints based on crops and beds compatibility.

    Uses `member` and `not_member` constraints.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    beds_data : BedsData
    beds_selection_func : Callable[[pd.Series, BedsData], Sequence[int] | Sequence[bool]]
        Filtering function taking a single crop data and generating the list of beds the contraint applies on.
    forbidden : bool
        If True, implements a negative constraint.
    """

    def __init__(
        self,
        crops_calendar: CropsCalendar,
        beds_data: BedsData,
        beds_selection_func: Callable[
            [pd.Series, BedsData], Sequence[int] | Sequence[bool]
        ],
        forbidden: bool = False,
    ):
        self.crops_calendar = crops_calendar
        self.beds_data = beds_data
        self.beds_selection_func = beds_selection_func
        self.forbidden = forbidden

    def build(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        constraints = []

        for crop_var, (_, crop_data) in zip(
            assignment_vars, self.crops_calendar.df_assignments.iterrows()
        ):
            crop_selected_beds = self.beds_selection_func(crop_data, self.beds_data)

            if len(crop_selected_beds) > 0:
                crop_selected_beds = list(map(int, crop_selected_beds))

                if self.forbidden:
                    crop_constraints = model.not_member(crop_var, crop_selected_beds)
                else:
                    crop_constraints = model.member(crop_var, crop_selected_beds)

                constraints.append(crop_constraints)

        return constraints

    def check_solution(self, solution: Solution) -> tuple[bool, list]:
        violated_constraints = []

        on = list(solution.crops_planning.columns.difference(["assignment"]))
        df = pd.merge(
            solution.crops_planning,
            solution.crops_calendar.df_assignments,
            on=on,
        )

        for _, crop_data in df.iterrows():
            crop_selected_beds = self.beds_selection_func(crop_data, self.beds_data)

            if len(crop_selected_beds) > 0:
                crop_selected_beds = list(map(int, crop_selected_beds))

                if self.forbidden and (crop_data["assignment"] in crop_selected_beds):
                    violated_constraints.append(crop_data)
                elif (not self.forbidden) and (crop_data["assignment"] not in crop_selected_beds):
                    violated_constraints.append(crop_data)

        return (len(violated_constraints) == 0), violated_constraints


class SuccessionConstraint(Constraint):
    """Implements temporal proximity constraints.

    Two implementations are available:
    - "pairwise": all constraints are binary equality or non-equality constraints
    - "cliques": uses all_different or all_equal constraints on maximal cliques

    Parameters
    ----------
    crops_calendar : CropsCalendar
    temporal_adjacency_graph : nx.Graph
        Graph representing the temporal proximity.
    forbidden : bool
        If True, implements a negative constraint.
    implementation : str, default="pairwise"
        If "pairwise" produces binary constraints on graph's edges, if "cliques" produces global constraints on cliques.
    """

    def __init__(
        self,
        crops_calendar: CropsCalendar,
        temporal_adjacency_graph: nx.Graph,
        forbidden: bool,
        implementation: str = "pairwise",
    ):
        self.crops_calendar = crops_calendar
        self.temporal_adjacency_graph = temporal_adjacency_graph
        self.forbidden = forbidden
        self.implementation = implementation

        build_funcs = {
            "pairwise": self._build_pairwise,
            "cliques": self._build_cliques,
        }
        if implementation not in build_funcs.keys():
            raise ValueError(
                f"'implementation' must take one of the following values: {list(build_funcs.keys())}"
            )
        self._build_func = build_funcs[implementation]

    def build(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        return self._build_func(model, assignment_vars)

    def _build_pairwise(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        constraints = []

        for i in self.temporal_adjacency_graph:
            for j in self.temporal_adjacency_graph[i]:
                if self.forbidden:
                    constraints.append(
                        assignment_vars[i] != assignment_vars[j]
                    )
                else:
                    constraints.append(
                        assignment_vars[i] == assignment_vars[j]
                    )

        return constraints

    def _build_cliques(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        constraints = []

        cliques = nx.find_cliques(self.temporal_adjacency_graph)
        for clique in cliques:
            overlapping_assignment_vars = assignment_vars[list(clique)]
            if self.forbidden:
                constraints.append(
                    model.all_different(overlapping_assignment_vars)
                )
            else:
                constraints.append(
                    model.all_equal(overlapping_assignment_vars)
                )

        return constraints

    def check_solution(self, solution: Solution) -> tuple[bool, list]:
        violated_constraints = []

        assignments = solution.crops_planning

        cliques = nx.find_cliques(self.temporal_adjacency_graph)
        for clique in cliques:
            df = assignments.iloc[list(clique)]
            groups = df.groupby("assignment").groups

            if self.forbidden:
                violations = {k : df.loc[v] for k, v in groups.items() if len(v) > 1}
            else:
                violations = {k : df.loc[v] for k, v in groups.items() if len(v) != len(clique)}

            if len(violations) > 0:
                violated_constraints.append(violations)

        return (len(violated_constraints) == 0), violated_constraints


class SuccessionConstraintWithReinitialisation(Constraint):
    """Implements temporal proximity constraints with reinitialisation.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    temporal_adjacency_graph : nx.Graph
        Graph representing the temporal proximity.
    forbidden : bool
        If True, implements a negative constraint.
    """

    def __init__(
        self,
        crops_calendar: CropsCalendar,
        temporal_adjacency_graph: nx.Graph,
        forbidden: bool,
    ):
        self.crops_calendar = crops_calendar
        self.temporal_adjacency_graph = temporal_adjacency_graph
        self.forbidden = forbidden

        intervals = crops_calendar.crops_calendar[:, 1:3]
        starting_weeks = intervals[:, 0]
        assert all(
            starting_weeks[i] <= starting_weeks[i + 1]
            for i in range(len(starting_weeks) - 1)
        )
        self.starting_weeks = starting_weeks

    def build(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        constraints = []

        for i in self.temporal_adjacency_graph:
            for j in self.temporal_adjacency_graph[i]:
                if i > j:
                    continue

                if self.forbidden:
                    if i + 1 == j:
                        constraints.append(
                            assignment_vars[i] != assignment_vars[j]
                        )
                    else:
                        candidates_ind = range(i + 1, j)

                        from pychoco.constraints.cnf.log_op import implies_op, or_op
                        constraints.append(
                            implies_op(
                                assignment_vars[i] == assignment_vars[j],
                                or_op(
                                    *(
                                        assignment_vars[k] == assignment_vars[i]
                                        for k in candidates_ind
                                    )
                                ),
                            )
                        )
                else:
                    raise NotImplementedError()

        return constraints

    # TODO
    def check_solution(self, solution: Solution) -> tuple[bool, list]:
        violated_constraints = []

        assignments = solution.crops_planning

        for i in self.temporal_adjacency_graph:
            for j in self.temporal_adjacency_graph[i]:
                if i > j:
                    continue

                a_i, a_j = assignments.iloc[i], assignments.iloc[j]
                min_start_week = min(a_i["starting_week"], a_j["starting_week"])
                max_start_week = max(a_i["starting_week"], a_j["starting_week"])
                if (
                    self.forbidden
                    and (a_i["assignment"] == a_j["assignment"])
                    and (not any((assignments["starting_week"] > min_start_week) & (assignments["starting_week"] < max_start_week) & (assignments["assignment"] == a_i["assignment"])))
                ):
                    violated_constraints.append([a_i, a_j])
                elif not self.forbidden:
                    raise NotImplementedError()

        return (len(violated_constraints) == 0), violated_constraints


class BinaryNeighbourhoodConstraint(Constraint):
    """Implements spatial proximity constraints for pairs of crops.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    adjacency_graph : nx.Graph
        Graph representing the spatial proximity.
    forbidden : bool
        If True, implements a negative constraint.
    """

    def __init__(
        self,
        crops_calendar: CropsCalendar,
        adjacency_graph: nx.Graph,
        forbidden: bool,
    ):
        self.crops_calendar = crops_calendar
        self.adjacency_graph = adjacency_graph
        self.forbidden = forbidden

    @abstractmethod
    def crops_selection_function(self, i: int, j: int) -> bool: ...

    def build(
        self,
        model: Model,
        assignment_vars: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        constraints = []

        for i, j in self.crops_calendar.overlapping_cultures_iter(2):
            if self.crops_selection_function(i, j):
                a_i, a_j = assignment_vars[i], assignment_vars[j]

                tuples = []
                for val1 in a_i.get_domain_values():
                    for val2 in self.adjacency_graph[val1]: # more general adjacency criteria? (node distance higher than 1? sharing the same connected component?)
                        tuples.append((val1, val2))

                constraints.append(
                    model.table([a_i, a_j], tuples, feasible=not self.forbidden)
                )

        return constraints

    def check_solution(self, solution: Solution) -> tuple[bool, list]:
        violated_constraints = []

        assignments = solution.crops_planning

        for i, j in self.crops_calendar.overlapping_cultures_iter(2):
            if self.crops_selection_function(i, j):
                a_i, a_j = assignments.iloc[i], assignments.iloc[j]

                if self.forbidden and self.adjacency_graph.has_edge(a_i["assignment"], a_j["assignment"]):
                    violated_constraints.append([a_i, a_j])
                elif (not self.forbidden) and (not self.adjacency_graph.has_edge(a_i["assignment"], a_j["assignment"])):
                    violated_constraints.append([a_i, a_j])

        return (len(violated_constraints) == 0), violated_constraints



class GroupNeighbourhoodConstraint(Constraint):
    """Implements spatial proximity constraints for groups of crops.

    Parameters
    ----------
    crops_calendar : CropsCalendar
    adjacency_graph : nx.Graph
        Graph representing the spatial proximity.
    forbidden : bool
        If True, implements a negative constraint.
    """

    def __init__(
        self,
        crops_groups: Sequence[Sequence[int]],
        adjacency_graph: nx.Graph,
        forbidden: bool,
    ):
        self.crops_groups = crops_groups
        self.adjacency_graph = adjacency_graph
        self.forbidden = forbidden

    def build(
        self,
        model: Model,
        assignment_variables: Sequence[IntVar],
    ) -> Sequence[ChocoConstraint]:
        constraints = []

        for crops_group in self.crops_groups:
            assert len(crops_group) > 0
            if len(crops_group) == 1:
                continue

            # TODO assumes first element in crops_group is lowest crop_id
            a_i = assignment_variables[crops_group[0]]
            crops_group_assignment_vars = [assignment_variables[i] for i in crops_group]

            allowed_tuples = []
            for val1 in a_i.get_domain_values():
                candidate_paths = nx.all_simple_paths(
                    self.adjacency_graph,
                    source=val1,
                    target=self.adjacency_graph.nodes,
                    cutoff=len(crops_group),
                )
                candidate_paths = list(
                    filter(lambda p: len(p) == len(crops_group), candidate_paths)
                )

                allowed_tuples += candidate_paths

            constraints.append(
                model.table(
                    crops_group_assignment_vars,
                    allowed_tuples,
                    feasible=not self.forbidden,
                )
            )

        return constraints

    def check_solution(self, solution: Solution) -> tuple[bool, list]:
        violated_constraints = []

        assignments = solution.crops_planning

        import networkx as nx
        for crops_group in self.crops_groups:
            beds = assignments.iloc[crops_group]["assignment"]

            subgraph = nx.induced_subgraph(self.adjacency_graph, beds)

            if self.forbidden and (len(subgraph.edges) > 0):
                violated_constraints.append(crops_group)
            elif (not self.forbidden) and (not nx.is_connected(subgraph)):
                violated_constraints.append(crops_group)

        return (len(violated_constraints) == 0), violated_constraints
