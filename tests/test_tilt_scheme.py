import pytest
from ..data.tilt_scheme import TiltScheme

def test_TiltSheme_test():
    scheme = TiltScheme([0])
    assert scheme.check(printf=print)
    scheme.append(-75)
    assert scheme.check(printf=print) is False