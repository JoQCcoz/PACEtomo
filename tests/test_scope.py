import pytest
from ..scope.interface_test import TestInterface

def test_update_state():
    scope = TestInterface()
    scope.update_state(ISX0=1,ISY0=1)
    assert scope.state._ISX0 == 1

    with pytest.raises(AttributeError) as e_info:
        scope.update_state(bla=1)


def test_initialize():
    scope = TestInterface()
    scope.initialize()
    assert all([scope.state._curDir is not None,scope.state._fileExt is not None, scope.state._fileStem is not None])