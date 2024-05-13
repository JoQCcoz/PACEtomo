import pytest
from ..functions.tilt_schemes import load_tilt_scheme_from_file, create_dose_symmetric_scheme
from pathlib import Path

def test_load_tilt_scheme_from_file():
    scheme = load_tilt_scheme_from_file(Path(Path(__file__).parent,'test_tilt_file.txt'))
    assert isinstance(scheme, list)
    assert all([isinstance(i,float) for i in scheme])
    assert scheme == [0,3,6,-3,-6]
