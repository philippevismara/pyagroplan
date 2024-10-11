import pytest

from constraints import Constraint


def test_abstract_constraint():
    with pytest.raises(TypeError):
        Constraint()
