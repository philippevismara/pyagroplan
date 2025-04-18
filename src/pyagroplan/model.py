from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Generator, Optional

    from pychoco.variables.intvar import IntVar

    from .solution import Solution

import numpy as np
from collections.abc import Mapping, Sequence

from pychoco import Model
from pychoco.solver import Solver as ChocoSolver
from pychoco.variables.boolvar import BoolVar
from pychoco.constraints.cnf.log_op import LogOp

from . import CropPlanProblemData
from .constraints.cp_constraints_pychoco import Constraint
from .solution import Solution


def _get_available_search_strategies() -> dict[str, Callable]:
    """Fetches all the search strategies implemented in Pychoco.

    Returns
    ------
    dict[str, Callable]
        Dictonary whose keys are the names of the search strategies and the values the fonction
        defining the strategy in the backend.
    """
    methods = [
        (method_name, getattr(ChocoSolver, method_name))
        for method_name in dir(ChocoSolver)
        if callable(getattr(ChocoSolver, method_name))
    ]

    available_search_strategies = {}
    for method_name, method_func in methods:
        import re
        match = re.fullmatch(r"^set_(.*)_search$", method_name)
        if match:
            search_name = match[1]
            # TODO update pychoco to avoid doing this manually
            if search_name == "default":
                default_method_func = method_func  # Necessary to avoid rewriting of variable before function call
                method_func = lambda solver, *_: default_method_func(solver)
            available_search_strategies[search_name] = method_func

    return available_search_strategies


#: Dictionnary of search strategies implemented in Pychoco
available_search_strategies = _get_available_search_strategies()

class AgroEcoPlanModel:
    """Global class used to configure and solve the model.

    Attributes
    ----------
    crop_plan_problem_data : CropPlanProblemData
        `CropPlanProblemData` used.
    n_assignments : int
        Number of assignments to make.
    n_beds : int
        Number of beds.
    verbose : bool
        Verbose output.
    model : Model
        Pychoco `Model` object used.
    assignment_vars : list[IntVar]
        List of Pychoco assignment variables.

    Parameters
    ----------
    crop_plan_problem_data : CropPlanProblemData
        `CropPlanProblemData` object used to define the model.
    verbose : bool, optional
        If True, verbose output.
    """

    def __init__(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        verbose: bool = False,
    ):
        beds_data = crop_plan_problem_data.beds_data
        crop_calendar = crop_plan_problem_data.crop_calendar

        model = Model()
        
        past_crop_plan_vars = []
        if crop_calendar.past_crop_plan:
            past_crop_plan_vars = model.intvars(
                crop_calendar.past_crop_plan.n_assignments,
                list(crop_calendar.past_crop_plan.allocated_bed_id),
                name="past_a",
            )
        # TODO update pychoco to avoid doing this here (creating a array of variables with same domain)
        future_assignment_vars = [
            model.intvar(beds_data.beds_ids, None, "{}_{}".format("a", i))
            for i in range(crop_calendar.n_future_assignments)
        ]

        self.crop_plan_problem_data = crop_plan_problem_data
        self.n_assignments = crop_plan_problem_data.crop_calendar.n_assignments
        self.n_beds = crop_plan_problem_data.beds_data.n_beds
        self.verbose = verbose

        self.model = model

        self.past_crop_plan_vars = past_crop_plan_vars
        self.future_assignment_vars = future_assignment_vars
        self.assignment_vars = np.asarray(
            self.past_crop_plan_vars
            + self.future_assignment_vars
        )

        self._constraints: dict[Constraint | str, Any] = {}

        
    def __str__(self) -> str:
        return "AgroEcoPlanModel(crop_plan_problem_data={}, verbose={})".format(
            self.crop_plan_problem_data,
            self.verbose,
        )


    def init(
        self,
        constraints: Mapping[str,Constraint]|Sequence[Constraint]|Constraint = tuple(),
    ) -> None:
        """Initialises the model with non-overlapping assignments constraints, symmetry breaking constraints and the constraints provided as parameter.

        Parameters
        ----------
        constraints :
            List of constraints to initialise the model with.
        """
        self._add_non_overlapping_assignments_constraints()
        self._break_symmetries()

        self.add_constraints(constraints)

    def add_constraints(
        self,
        constraints: Mapping[str,Constraint]|Sequence[Constraint]|Constraint = tuple(),
        name: Optional[str] = None,
    ) -> None:
        if isinstance(constraints, Mapping):
            for name, constraint in constraints.items():
                self.add_constraints(constraint, name=name)
        elif isinstance(constraints, Sequence):
            for constraint in constraints:
                self.add_constraints(constraint)
        else:
            self.add_constraint(constraints, name=name)


    def add_constraint(
        self,
        constraint: Constraint,
        name: Optional[str]=None,
    ) -> None:
        """Adds a constraint to the model.

        Parameters
        ----------
        constraint :
            Constraints to add in the model.

        Raises
        ------
        ValueError
            If `constraint` is not a valid constraint that can be posted.
        """
        constraints = constraint.build(self.model, self.assignment_vars)
        for cstr in constraints:
            if hasattr(cstr, "post") and callable(cstr.post):
                cstr.post()
            elif isinstance(cstr, BoolVar):
                self.model.add_clause_true(cstr)
            elif isinstance(cstr, LogOp):
                self.model.add_clauses_logop(cstr)
            else:
                raise ValueError(f"unknown constraint type {type(cstr)}")

        if name:
            self._constraints[name] = constraints
        else:
            self._constraints[constraint] = constraints

    def set_objective_function(self, variable: IntVar, maximize: bool) -> None:
        raise NotImplementedError()
        self.model.set_objective(variable, maximize)

    def configure_solver(self, search_strategy: str = "default") -> None:
        """Configures the solver and the search strategy to use.

        Parameters
        ----------
        search_strategy :
            Search strategy to use.

        Raises
        ------
        ValueError
            If `search_strategy` is not a valid search strategy implemented in Pychoco.
        """
        self.solver = self.model.get_solver()

        if search_strategy not in available_search_strategies:
            raise ValueError(f"search strategy {search_strategy} unknown")

        func = available_search_strategies[search_strategy]
        func(self.solver, *self.assignment_vars)

    def solve(self, **kwargs: Any) -> Solution:
        """Attempts to solve the model.

        Parameters
        ----------
        kwargs :
            Arguments to pass to Pychoco's solver solve() function.

        Raises
        ------
        RuntimeError
            If no solution can be found.

        Returns
        -------
        Solution
        """
        if not hasattr(self, "solver"):
            self.configure_solver()

        has_solution = self.solver.solve(**kwargs)
        if not has_solution:
            raise RuntimeError("No solution found")
        else:
            variables_values = self._extract_variables_values(self.assignment_vars)
            return Solution(self.crop_plan_problem_data, variables_values)

    def _extract_variables_values(self, variables: Sequence[IntVar]) -> list[int]:
        """Extracts the instantiated values of the variables.

        Parameters
        ----------
        variables :
            List of variables.

        Returns
        -------
        List of ints
        """
        #variables_names = [var.name for var in variables]
        variables_values = [var.get_value() for var in variables]
        # TODO variables = choco_solution.retrieveIntVars()
        return variables_values

    def iterate_over_all_solutions(self) -> Generator[Solution]:
        """Iterator over all solutions.

        Yields
        -------
        Solution
        """
        while True:
            try:
                yield self.solve()
            except RuntimeError:
                break

    def _add_non_overlapping_assignments_constraints(self) -> None:
        """Adds non-overlapping assignments constraints as part of the basic model definition."""
        constraints = []

        for overlapping_crops in self.crop_plan_problem_data.crop_calendar.crops_overlapping_cultivation_intervals:
            overlapping_assignment_vars = self.assignment_vars[list(overlapping_crops)]

            constraint = self.model.all_different(overlapping_assignment_vars)
            constraint.post()

            constraints.append(constraint)

        self._constraints["non_overlapping_assignments_constraints"] = constraints


    def _break_symmetries(self) -> None:
        """Adds symmetry-breaking constraints as part of the basic model definition.

        The symmetry-breaking constraints consist of `increasing` constraints on
        assignment variables part of the same cropping group.
        """
        constraints = []

        for group in self.crop_plan_problem_data.crop_calendar.crops_groups_assignments:
            assert len(group) > 0
            if len(group) > 1:
                group_vars = self.assignment_vars[group]

                # Do not apply symmetry breaking if variables are already instanciated (i.e., past crop plan)
                if max([len(v.get_domain_values()) for v in group_vars]) == 1:
                    continue

                constraint = self.model.increasing(group_vars, True)
                constraint.post()
                constraints.append(constraint)

        self._constraints["symmetry_breaking_constraints"] = constraints


    def print_constraints_statistics(self) -> None:
        for constraint_obj, cp_constraints in self._constraints.items():
            if isinstance(constraint_obj, str):
                constraint_name = constraint_obj
            else:
                constraint_name = constraint_obj.__class__.__name__

            if len(cp_constraints) > 0:
                if hasattr(cp_constraints[0], "get_name"):
                    constraint_type = cp_constraints[0].get_name()
                else:
                    constraint_type = cp_constraints[0]
                print(f"{constraint_name}: {len(cp_constraints)} constraints of type '{constraint_type}'")
            else:
                print(f"{constraint_name}: {len(cp_constraints)} constraints")
