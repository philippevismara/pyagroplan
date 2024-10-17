from abc import ABC, abstractmethod

from interval_graph import interval_graph_rotation


class Constraint(ABC):
    @abstractmethod
    def build(self, model, assignment_vars): ...


class CropsRotationConstraint(Constraint):
    def __init__(self, crops_calendar):
        self.crops_calendar = crops_calendar
        self.return_delay = self.crops_calendar.df_assignments["delai_retour"].values
        self.families = self.crops_calendar.df_assignments["famille"].values

        intervals = self.crops_calendar.crops_calendar[:, 1:].astype(int)
        intervals[:, -1] += self.return_delay
        self.interval_graph = interval_graph_rotation(list(map(list, intervals)), self.families)

    def build(self, model, assignment_vars):
        constraints = []

        for node_i in self.interval_graph:
            i, *_ = node_i
            for node_j in self.interval_graph.neighbors(node_i):
                j, *_ = node_j
                constraints.append(
                    model.arithm(assignment_vars[i], "!=", assignment_vars[j])
                )

        return constraints


class ForbidNegativeInteractionsConstraint(Constraint):
    def __init__(
            self,
            crops_calendar,
            beds_data,
            implementation="distance",
    ):
        self.crops_overlapping_intervals = crops_calendar.crops_overlapping_cultivation_intervals
        self.crops_interactions = crops_calendar.crops_data.crops_interactions
        self.crops_names = crops_calendar.crops_names
        self.beds_data = beds_data
        self.implementation = implementation

        build_funcs = {
            # "explicitly": self._build_explicitly,
            "table": self._build_table,
            "distance": self._build_distance,
        }
        if self.implementation not in build_funcs:
            raise ValueError()

        self.build_func = build_funcs[self.implementation]

    def build(self, model, assignment_vars):
        return self.build_func(model, assignment_vars)

    def _build_explicitly(self, model, assignment_vars):
        # TODO does this really work? (calling adjacency function with IntVars?)
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0
                ):
                    constraints.append(
                        self.beds_data.adjacency_function(a_i, a_j) == False
                    )

        return constraints

    def _build_table(self, model, assignment_vars):
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0
                ):
                    forbidden_tuples = []
                    for val1 in a_i.get_domain_values():
                        for val2 in self.beds_data.adjacency_matrix[val1]:
                            forbidden_tuples.append((val1, val2))
                    constraints.append(
                        model.table([a_i, a_j], forbidden_tuples, feasible=False)
                    )

        return constraints

    def _build_distance(self, model, assignment_vars):
        # TODO prune useless constraints manually (or automatically ?)
        # TODO stronger constraint then needed
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_names[i], self.crops_names[j]) < 0
                ):
                    constraints.append(
                        model.distance(a_i, a_j, ">", 1)
                    )

        return constraints


class AdjacencyConstraint(Constraint):
    def __init__(self, crops_calendar, beds_data, forbid):
        self.crops_overlapping_intervals = crops_calendar.crops_overlapping_cultivation_intervals
        self.beds_data = beds_data
        self.forbid = forbid

    @abstractmethod
    def selection_function(self, i, j): ...

    def build(self, model, assignment_vars):
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.selection_function(i, j)
                ):
                    tuples = []
                    for val1 in a_i.get_domain_values():
                        for val2 in self.beds_data.adjacency_matrix[val1]:
                            tuples.append((val1, val2))

                    constraints.append(
                        model.table([a_i, a_j], tuples, feasible=not self.forbid)
                    )

        return constraints


class DiluteSpeciesConstraint(AdjacencyConstraint):
    def __init__(self, crops_calendar, beds_data):
        super().__init__(crops_calendar, beds_data, forbid=True)
        self.crops_species = crops_calendar.crops_names

    def selection_function(self, i, j):
        return self.crops_species[i] == self.crops_species[j]


class DiluteFamilyConstraint(AdjacencyConstraint):
    def __init__(self, crops_calendar, beds_data):
        super().__init__(crops_calendar, beds_data, forbid=True)
        self.crops_families = crops_calendar.df_assignments["famille"].values

    def selection_function(self, i, j):
        return self.crops_families[i] == self.crops_families[j]


class GroupIdenticalCropsConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model, assignment_variables):
        raise NotImplementedError()


"""
TODO handle optimization objective
class InteractionConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model, assignment_vars):
        raise NotImplementedError()
"""


"""
TODO what is this constraint ? (added after paper)
class ForbidNegativePrecedencesConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model, assignment_vars):
        raise NotImplementedError()
"""


"""
TODO

public:
postInteractionReifTable
postInteractionReifBased

private:
postInteractionCountBased
postInteractionCustomPropBased
postInteractionGraphBased
"""
