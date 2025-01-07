from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Callable, Generator

    from pychoco.variables import IntVar

    from .beds_data import BedsData
    from .constraints.cp_constraints_pychoco import Constraint
    from .crops_calendar import CropsCalendar
    from .solution import Solution

import numpy as np
from pychoco import Model
from pychoco.solver import Solver as ChocoSolver
from pychoco.variables.boolvar import BoolVar
from pychoco.constraints.cnf.log_op import LogOp

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
                method_func = lambda solver, *_: method_func(solver)
            available_search_strategies[search_name] = method_func

    return available_search_strategies


#: Dictionnary of search strategies implemented in Pychoco
available_search_strategies = _get_available_search_strategies()


class AgroEcoPlanModel:
    """Global class used to configure and solve the model.

    Attributes
    ----------
    crops_calendar : CropsCalendar
        `CropsCalendar` used.
    beds_data : BedsData
        `BedsData` used.
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
    crops_calendar : CropsCalendar
        `CropsCalendar` object used to define the model.
    beds_data : BedsData
        `BedsData` object used to define the model.
    verbose : bool, optional
        If True, verbose output.
    """

    def __init__(
        self,
        crops_calendar: CropsCalendar,
        beds_data: BedsData,
        verbose: bool = False,
    ):
        self.crops_calendar = crops_calendar
        self.beds_data = beds_data
        self.n_assignments = self.crops_calendar.n_assignments
        self.n_beds = self.beds_data.n_beds
        self.verbose = verbose

        self.model = Model()
        """
        TODO add fixed domains (pre-allocated beds) + forbidden beds
        can't we add constraints instead? (less efficient?)

        :meta private:
        """
        # TODO update pychoco to avoid doing this here
        self.assignment_vars = [
            self.model.intvar(self.beds_data.beds_ids, None, "{}_{}".format("a", i))
            for i in range(self.n_assignments)
        ]
        self.assignment_vars = np.asarray(self.assignment_vars)

    def __str__(self) -> str:
        return "AgroEcoPlanModel(crop_calendar={}, beds_data={}, verbose={})".format(
            self.crops_calendar,
            self.beds_data,
            self.verbose,
        )

    def init(self, constraints: Sequence[Constraint] = tuple()) -> None:
        """Initialises the model with non-overlapping assignments constraints, symmetry breaking constraints and the constraints provided as parameter.

        Parameters
        ----------
        constraints :
            List of constraints to initialise the model with.
        """
        self._add_non_overlapping_assignments_constraints()
        self._break_symmetries()

        for constraint in constraints:
            self.add_constraint(constraint)

    def add_constraint(self, constraint: Constraint) -> None:
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

    def solve(self) -> Solution:
        """Attempts to solve the model.

        Raises
        ------
        RuntimeError
            If no solution can be found.

        Returns
        -------
        Solution
        """
        has_solution = self.solver.solve()
        if not has_solution:
            raise RuntimeError("No solution found")
        else:
            variables_values = self._extract_variables_values(self.assignment_vars)
            return Solution(self.crops_calendar, variables_values)

    def _extract_variables_values(self, variables: Sequence[IntVar]) -> list[int]:
        """Extacts the instantiated values of the variables.

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
        for overlapping_crops in self.crops_calendar.crops_overlapping_cultivation_intervals:
            overlapping_assignment_vars = self.assignment_vars[list(overlapping_crops)]
            self.model.all_different(overlapping_assignment_vars).post()

    def _break_symmetries(self) -> None:
        """Adds symmetry-breaking constraints as part of the basic model definition.

        The symmetry-breaking constraints consist of `increasing` constraints on
        assignment variables part of the same cropping group.
        """

        for group in self.crops_calendar.crops_groups_assignments:
            # TODO remove len(group) == 1
            assert len(group) > 0
            group_vars = self.assignment_vars[group]
            self.model.increasing(group_vars, True).post()

    # TODO initNumberOfPositivePrecedences
    # TODO initNumberOfPositivePrecedencesCountBased
