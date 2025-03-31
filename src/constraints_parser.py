from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable

import warnings
from abc import ABC, abstractmethod
import datetime

import pandas as pd

from ._typing import FilePath


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
        matrices = {
            name: self.build_matrix_from_constraint_func(
                df_data,
                self.parse_rule(**definition),
            )
            for name, definition in def_dict.items()
        }

        for name, matrix in matrices.items():
            if (
                (matrix == "").all(axis=None)
                or (matrix == datetime.timedelta(weeks=0)).all(axis=None)
            ):
                warnings.warn(
                    f"Empty constraint matrix, thus does not constrain the model (constraint name: {name})"
                )

        return matrices


    def build_matrix_from_constraint_func(
        self,
        df_data: pd.DataFrame,
        constraint_func: Callable,
    ) -> pd.DataFrame:
        df_matrix = df_data.apply(constraint_func, axis=1, args=(df_data,))
        df_matrix.index = df_data.index
        df_matrix.columns = df_data.index
        return df_matrix



class PrecedenceConstraintDefinitionsParser(ConstraintDefinitionsParser):
    def parse_rule_str(
        self,
        rule_str: str,
        value: Any,
        default_value: Any,
        **kwargs: Any,
    ) -> Callable:
        rule_str = rule_str.strip()

        rule_str = rule_str.replace("preceding_crop", "row_data")
        rule_str = rule_str.replace("following_crop", "df_data")

        def rule_func(row_data, df_data):
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


class SpatialInteractionsConstraintDefinitionsParser(ConstraintDefinitionsParser):
    def parse_rule_str(
        self,
        rule_str: str,
        value: Any,
        default_value: Any,
        **kwargs: Any,
    ) -> Callable:
        rule_str = rule_str.strip()

        rule_str = rule_str.replace("crop1", "row_data")
        rule_str = rule_str.replace("crop2", "df_data")
        rule_str = rule_str.replace("\n", "")

        def rule_func(row_data, df_data):
            res = pd.Series(index=df_data.index, dtype=str)
            res[:] = default_value
            ind = eval(rule_str)
            res[ind] = self.parse_value_str(value, row_data, df_data[ind])
            return res

        return rule_func

    def parse_value_str(self, value_str: str, row_data: pd.Series, df_data: pd.DataFrame) -> str:
        # [1,3][-crop2["harvesting_time"]-4,-crop2["harvesting_time"]-1]
        value_str = value_str.strip()

        value_str = value_str.replace("crop1", "row_data")
        value_str = value_str.replace("crop2", "df_data")
        value_str = value_str.replace("\n", "")

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
        # TODO adjacency_type

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
        value = kwargs["intervals_overlap"]
        #value = self.parse_value_str(kwargs["intervals_overlap"])
        value = type + value

        rule_str = kwargs["rule"]
        
        rule = self.parse_rule_str(rule_str, value, default_value, **kwargs)

        return rule
