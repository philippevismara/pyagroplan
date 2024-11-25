import pytest

from src.constraints import cp_constraints_pychoco as cstrs


def test_abstract_constraint():
    with pytest.raises(TypeError):
        cstrs.Constraint()
