from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable, Optional

    from . import CropPlanProblemData
    from .constraints.cp_constraints_pychoco import Constraint

import warnings
from abc import ABC, abstractmethod
import datetime

import numpy as np
import pandas as pd

from ._typing import FilePath
from .constraints import constraints as cstrs


def _preprocess_evaluated_str(eval_str: str) -> str:
    import textwrap
    eval_str = textwrap.dedent(eval_str)
    eval_str = eval_str.replace("\n", " ")
    eval_str = eval_str.strip()
    return eval_str


class ConstraintDefinitionsParser(ABC):
    @abstractmethod
    def parse_rule_str(
        self,
        rule_str: str,
        value: Any,
        default_value: Any,
        **kwargs: Any,
    ) -> Callable:
        ...

    @abstractmethod
    def parse_rule(self, **kwargs: Any) -> Callable:
        ...

    @abstractmethod
    def build_constraint_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        name: Optional[str]=None,
        *args: Any,
        **kwargs: Any,
    ) -> Constraint:
        ...

    def build_constraints_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Constraint]:
        return {
            constraint_name: self.build_constraint_from_definition_dict(
                crop_plan_problem_data,
                definition,
                constraint_name,
                *args,
                **kwargs,
            )
            for constraint_name, definition in def_dict.items()
        }

    def build_matrices_from_definition_file(
        self,
        df_data: pd.DataFrame,
        filename: FilePath,
    ) -> dict[str, pd.DataFrame]:
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(filename)

        def_dict = dict(cfg)
        del def_dict["DEFAULT"]

        return self.build_matrices_from_definition_dict(df_data, def_dict)


    def build_matrices_from_definition_dict(
        self,
        df_data: pd.DataFrame,
        def_dict: dict,
    ) -> dict[str, pd.DataFrame]:
        return {
            name: self.build_matrix_from_definition_dict(
                df_data,
                definition,
                name=name,
            )
            for name, definition in def_dict.items()
        }

    def build_matrix_from_definition_dict(
        self,
        df_data: pd.DataFrame,
        definition_dict: dict,
        name: Optional[str]=None,
    ) -> pd.DataFrame:
        df_matrix = df_data.apply(
            self.parse_rule(**definition_dict),
            axis=1,
            args=(df_data,),
        )
        df_matrix.index = df_data.index
        df_matrix.columns = df_data.index

        if (
            (df_matrix == "").all(axis=None)
            or (df_matrix == datetime.timedelta(weeks=0)).all(axis=None)
        ):
            warnings.warn(
                f"Empty constraint matrix, thus does not constrain the model (constraint name: {name})"
            )

        return df_matrix


class CompatibleBedsConstraintDefinitionsParser(ConstraintDefinitionsParser):
    def parse_rule_str(
        self,
        rule_str: str,
        value: Any,
        default_value: Any,
        **kwargs: Any,
    ) -> Callable:
        rule_str = _preprocess_evaluated_str(rule_str)

        def rule_func(row_data, df_data):
            preceding_crop = row_data
            following_crop = df_data

            res = pd.Series(index=df_data.index, dtype=object)
            res[:] = default_value
            ind = eval(rule_str)
            res[ind] = value

            return res

        return rule_func

    def parse_rule(self, **kwargs: Any) -> Callable:
        type = kwargs["type"]
        if type == "forbidden":
            type = "-"
        elif type == "enforced":
            type = "+"
        else:
            raise ValueError(
                f"Precedence interaction constraint type must be either "
                f"'forbidden' or 'enforced', given {type}."
            )

        default_value = datetime.timedelta(days=0)
        #precendence_effect_delay = kwargs["precedence_effect_delay"]
        #value = eval(f"datetime.timedelta({precendence_effect_delay})")
        value = datetime.timedelta(weeks=int(type + kwargs["precedence_effect_delay_in_weeks"]))

        rule_str = kwargs["rule"]

        rule = self.parse_rule_str(rule_str, value, default_value, **kwargs)
        return rule

    def build_constraint_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        name: Optional[str]=None,
        *args: Any,
        **kwargs: Any,
    ) -> Constraint:
        type = def_dict["type"]
        if type == "forbidden":
            forbidden = True
        elif type == "enforced":
            forbidden = False
        else:
            raise ValueError(
                f"Location constraint type must be either "
                f"'forbidden' or 'enforced', given {type}."
            )

        beds_selection_rule = def_dict["beds_selection_rule"]
        beds_selection_rule = _preprocess_evaluated_str(beds_selection_rule)
        crops_selection_rule = def_dict["crops_selection_rule"]
        crops_selection_rule = _preprocess_evaluated_str(crops_selection_rule)

        df_beds = crop_plan_problem_data.beds_data.df_beds_data
        def beds_selection_func(crop, beds_data):
            bed = beds_data.df_beds_data
            if eval(crops_selection_rule):
                return df_beds["bed_id"][np.where(
                    eval(beds_selection_rule)
                )[0]].values

            return []

        return cstrs.LocationConstraint(
            crop_plan_problem_data,
            beds_selection_func,
            forbidden=forbidden,
        )


class PrecedenceConstraintDefinitionsParser(ConstraintDefinitionsParser):
    def parse_rule_str(
        self,
        rule_str: str,
        value: Any,
        default_value: Any,
        **kwargs: Any,
    ) -> Callable:
        rule_str = _preprocess_evaluated_str(rule_str)

        def rule_func(row_data, df_data):
            preceding_crop = row_data
            following_crop = df_data

            res = pd.Series(index=df_data.index, dtype=object)
            res[:] = default_value
            ind = eval(rule_str)
            res[ind] = value
            return res

        return rule_func

    def parse_rule(self, **kwargs: Any) -> Callable:
        type = kwargs["type"]
        if type == "forbidden":
            type = "-"
        elif type == "enforced":
            type = "+"
        else:
            raise ValueError(
                f"Precedence constraint type must be either "
                f"'forbidden' or 'enforced', given {type}."
            )

        default_value = datetime.timedelta(days=0)
        #precendence_effect_delay = kwargs["precedence_effect_delay"]
        #value = eval(f"datetime.timedelta({precendence_effect_delay})")
        value = datetime.timedelta(weeks=int(type + kwargs["precedence_effect_delay_in_weeks"]))

        rule_str = kwargs["rule"]

        rule = self.parse_rule_str(rule_str, value, default_value, **kwargs)
        return rule

    def build_constraint_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        name: Optional[str]=None,
        *args: Any,
        **kwargs: Any,
    ) -> Constraint:
        matrix = self.build_matrix_from_definition_dict(
            crop_plan_problem_data.crop_calendar.df_assignments,
            def_dict,
            name=name,
        )

        if def_dict["type"] == "forbidden":
            return cstrs.PrecedencesConstraint(
                crop_plan_problem_data,
                matrix,
                *args,
                forbidden=True,
                **kwargs,
            )
        elif def_dict["type"] == "enforced":
            return cstrs.PrecedencesConstraint(
                crop_plan_problem_data,
                matrix,
                *args,
                forbidden=False,
                **kwargs,
            )
        else:
            raise NotImplementedError()


class SpatialInteractionsConstraintDefinitionsParser(ConstraintDefinitionsParser):
    def parse_rule_str(
        self,
        rule_str: str,
        value: Any,
        default_value: Any,
        **kwargs: Any,
    ) -> Callable:
        rule_str = _preprocess_evaluated_str(rule_str)

        def rule_func(row_data, df_data):
            crop1 = row_data
            crop2 = df_data

            res = pd.Series(index=df_data.index, dtype=str)
            res[:] = default_value
            ind = eval(rule_str)
            res[ind] = self.parse_value_str(value, row_data, df_data[ind])
            return res

        return rule_func

    def parse_value_str(self, value_str: str, row_data: pd.Series, df_data: pd.DataFrame) -> str:
        # [1,3][-crop2["harvesting_time"]-4,-crop2["harvesting_time"]-1]
        value_str = _preprocess_evaluated_str(value_str)

        crop1 = row_data
        crop2 = df_data

        import re
        int_pattern = r"[+-]?[0-9]+"
        interval_pattern = r"\[(.+),(.+)\]"
        m = re.match(
            rf"^([\+-]){interval_pattern}\w*{interval_pattern}$",
            value_str,
        )
        if not m:
            raise ValueError(
                f"Can not process value string in spatial constraint definition: {value_str}"
            )

        sign, s1, e1, s2, e2 = m.groups()
        res = sign + "["
        if re.fullmatch(int_pattern, s1.strip()):
            res += s1
        else:
            res += (eval(s1)).astype(int).astype(str)
        res += ","
        if re.fullmatch(int_pattern, e1.strip()):
            res += e1
        else:
            res += (eval(e1)).astype(int).astype(str)
        res += "]["
        if re.fullmatch(int_pattern, s2.strip()):
            res += s2
        else:
            res += (eval(s2)).astype(int).astype(str)
        res += ","
        if re.fullmatch(int_pattern, e2.strip()):
            res += e2
        else:
            res += (eval(e2)).astype(int).astype(str)
        res += "]"

        return res


    def parse_rule(self, **kwargs: Any) -> Callable:
        default_value = ""
        type = kwargs["type"]
        if type == "forbidden":
            type = "-"
        elif type == "enforced":
            type = "+"
        else:
            raise ValueError(
                f"Spatial interaction constraint type must be either "
                f"'forbidden' or 'enforced', given {type}."
            )
        value = kwargs.get("intervals_overlap", "[1,-1][1,-1]")
        #value = self.parse_value_str(kwargs["intervals_overlap"])
        value = type + value

        rule_str = kwargs["rule"]
        
        rule = self.parse_rule_str(rule_str, value, default_value, **kwargs)

        return rule


    def build_constraint_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        name: Optional[str]=None,
        *args: Any,
        **kwargs: Any,
    ) -> Constraint:
        matrix = self.build_matrix_from_definition_dict(
            crop_plan_problem_data.crop_calendar.df_assignments,
            def_dict,
            name=name,
        )

        if def_dict["type"] == "forbidden":
            return cstrs.SpatialInteractionsSubintervalsConstraint(
                crop_plan_problem_data,
                matrix,
                *args,
                adjacency_name=def_dict["adjacency_type"],
                forbidden=True,
                **kwargs,
            )
        elif def_dict["type"] == "enforced":
            return cstrs.SpatialInteractionsSubintervalsConstraint(
                crop_plan_problem_data,
                matrix,
                *args,
                adjacency_name=def_dict["adjacency_type"],
                forbidden=False,
                **kwargs,
            )
        else:
            raise NotImplementedError()


class ReturnDelaysConstraintParser:
    def build_constraint_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        name: Optional[str]=None,
        *args: Any,
        **kwargs: Any,
    ) -> Constraint:
        return cstrs.ReturnDelaysConstraint(
            crop_plan_problem_data,
            return_delays=def_dict["return_delays"],
        )


class GroupCropsConstraintDefinitionParser:
    def groupby_crops(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        groupby: str,
    ) -> list:
        df_assignments = crop_plan_problem_data.crop_calendar.df_assignments
        n_future_crops = len(crop_plan_problem_data.crop_calendar.df_future_crop_calendar)

        crops_groups_assignments = list(
            df_assignments.groupby(
                groupby,
                sort=False,
            ).indices.values()
        )
        future_crops_groups_assignments = crops_groups_assignments[-n_future_crops:]
        return future_crops_groups_assignments

    def filter_crops_groups(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        crops_groups: list,
        filtering_rule_str: str,
    ) -> list:
        filtering_rule_str = _preprocess_evaluated_str(filtering_rule_str)

        # FIXME this only works with "crop_group_id"
        crop = crop_plan_problem_data.crop_calendar.df_future_crop_calendar
        ind = eval(filtering_rule_str)
        
        crops_groups = np.asarray(crops_groups, dtype=object)[ind]
        return list(crops_groups)

    def build_constraint_from_definition_dict(
        self,
        crop_plan_problem_data: CropPlanProblemData,
        def_dict: dict,
        name: Optional[str]=None,
        *args: Any,
        **kwargs: Any,
    ) -> Constraint:
        crops_groups = self.groupby_crops(
            crop_plan_problem_data,
            def_dict["group_by"],
        )

        if "filtering_rule" in def_dict:
            crops_groups = self.filter_crops_groups(
                crop_plan_problem_data,
                crops_groups,
                def_dict["filtering_rule"],
            )

        return cstrs.GroupCropsConstraint(
            crop_plan_problem_data,
            crops_groups,
            adjacency_name=def_dict["adjacency_type"],
        )


_available_parsers = {
    "precedence_constraint": PrecedenceConstraintDefinitionsParser,
    "return_delays_constraint": ReturnDelaysConstraintParser,
    "spatial_interactions_constraint": SpatialInteractionsConstraintDefinitionsParser,
    "compatible_beds_constraint": CompatibleBedsConstraintDefinitionsParser,
    "group_crops_constraint": GroupCropsConstraintDefinitionParser,
}

def load_constraints(
    crop_plan_problem_data: CropPlanProblemData,
    definitions_dict: dict[str, Any],
) -> dict[str, Constraint]:
    constraints = {}

    for name, def_dict in definitions_dict.items():
        if "constraint_type" not in def_dict:
            raise KeyError("`constraint_type` field required in constraints definitions")

        constraint_type = def_dict["constraint_type"]

        if constraint_type not in _available_parsers:
            raise ValueError(
                f"`constraint_type` should be one of `{list(_available_parsers.keys())}` (given `{constraint_type}`)"
            )

        constraint_parser_cls = _available_parsers[constraint_type]
        constraint = constraint_parser_cls().build_constraint_from_definition_dict(
            crop_plan_problem_data,
            def_dict,
            name,
        )

        constraints[name] = constraint

    return constraints
