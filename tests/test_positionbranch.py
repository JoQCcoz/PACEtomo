import pytest
from ..data.position import PositionBranch

def test_skip_setter():
    pos = PositionBranch()
    with pytest.raises(TypeError) as e_info:
        pos.skip= 1
    print(e_info.value.args[0])

def test_set_params():
    pos = PositionBranch()
    pos.set_params(skip=True)
    assert pos.skip, True

    pos.set_params(skip=False,SSX=3.0)
    assert all([pos.SSX==3.0,pos.skip==False]), True

    with pytest.raises(AttributeError) as e_info:
        pos.set_params(bla=1)
    print(e_info.value.args[0])

# def tes