import pytest

from nattrs import nested_hasattr


def test_nested_hasattr_examples():
    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {"d": 1}

    # Add to a dict 'a'
    a = {"b": B()}

    # Check presence of the member 'd'
    assert nested_hasattr(a, "b.c.d")

    # Fail to find member 'o'
    assert not nested_hasattr(a, "b.o.p")

    # object is None
    assert not nested_hasattr(None, "b.o.p", allow_none=True)
    with pytest.raises(TypeError):
        assert nested_hasattr(None, "b.o.p", allow_none=False)

    assert nested_hasattr(a, "b.{.*}.d", regex=True)
    assert not nested_hasattr(a, "b.{.*}.r", regex=True)
