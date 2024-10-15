from abc import ABC, abstractmethod


class Constraint(ABC):
    @abstractmethod
    def build(self, model): ...


class CropRotationConstraint(Constraint):
    def __init__(self, crops_data, return_delay):
        self.crops_data = crops_data
        self.return_delay = return_delay

    def build(self, model):
        raise NotImplementedError()


class ForbidNegativeInteractionsConstraint(Constraint):
    def __init__(
            self,
            crop_calendar,
            beds_data,
            implementation="distance",
    ):
        self.crops_overlapping_intervals = crop_calendar.crops_overlapping_cultivation_intervals
        self.crops_interactions = crop_calendar.crops_data.crops_interactions
        self.crops_name = crop_calendar.crops_name
        self.beds_data = beds_data
        self.implementation = implementation

        build_funcs = {
            "explicitly": self._build_explicitly,
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
                    and self.crops_interactions(self.crops_name[i], self.crops_name[j]) < 0
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
                    and self.crops_interactions(self.crops_name[i], self.crops_name[j]) < 0
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
        constraints = []

        for i, a_i in enumerate(assignment_vars):
            for j, a_j in enumerate(assignment_vars[i+1:], i+1):
                if (
                    any(frozenset((i, j)) <= interval for interval in self.crops_overlapping_intervals)
                    and self.crops_interactions(self.crops_name[i], self.crops_name[j]) < 0
                ):
                    constraints.append(
                        model.distance(a_i, a_j, ">", 1)
                    )

        return constraints


class DiluteSpeciesConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model):
        raise NotImplementedError()


class DiluteFamilyConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model):
        raise NotImplementedError()


class GroupIdenticalCropsConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build_constraint(self, assignment_variables):
        raise NotImplementedError()


class InteractionConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model):
        raise NotImplementedError()


class ForbidNegativePrecedencesConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def build(self, model):
        raise NotImplementedError()


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
