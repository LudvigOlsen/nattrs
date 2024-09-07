import re
import pytest

from nattrs import nested_getattr
from nattrs.utils import Ignore


def test_nested_getattr_examples():
    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {"d": 1}

    # Add to a dict 'a'
    a = {"b": B()}

    # Get the value of 'd'
    assert nested_getattr(a, "b.c.d") == 1

    # Get default value when not finding an attribute
    assert nested_getattr(a, "b.o.p", default="not found") == "not found"

    # object is None
    assert nested_getattr(None, "b.o.p", allow_none=True) is None
    with pytest.raises(TypeError):
        assert nested_getattr(None, "b.o.p", allow_none=False)

    assert nested_getattr(a, "b.{.*}.{.*}", regex=True) == {"b.c.d": 1}


def test_nested_getattr_regex():
    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {"e": 1, "f": 3}
            self.d = {"e": 4, "g": 7}

    # Add to a dict 'a'
    a = {"b": B()}

    print("Using multiple regex:")
    print(nested_getattr(a, "b.{.*}.{.*}", regex=True))
    nested_getattr(a, "b.{.*}.{.*}", regex=True) == {
        "b.c.e": 1,
        "b.c.f": 3,
        "b.d.e": 4,
        "b.d.g": 7,
    }

    # Ignores default when finding matches
    nested_getattr(a, "b.{.*}.{.*}", default="hello", regex=True) == {
        "b.c.e": 1,
        "b.c.f": 3,
        "b.d.e": 4,
        "b.d.g": 7,
    }

    # Defaults to empty dict when nothing is found
    print("When nothing found:")
    print(nested_getattr(a, "b.o.{.*}.{.*}", default="hello", regex=True))
    nested_getattr(a, "b.o.{.*}.{.*}", default="hello", regex=True) == {}

    # object is None
    assert nested_getattr(None, "b.o.{.*}", allow_none=True, regex=True) is None
    with pytest.raises(TypeError):
        assert nested_getattr(None, "b.o.{.*}", allow_none=False, regex=True)

    a = {"b": {"c": {"d": 1}, "e": {"f": 2}}}
    result = nested_getattr(a, "b.{.*}.w", regex=True)
    assert result == {
        "b.c.w": None,
        "b.e.w": None,
    }

    # Ignore non-existing values
    result = nested_getattr(a, "b.{.*}.w", default=Ignore(), regex=True)
    assert result == {}

    # No match should return an empty dict
    result = nested_getattr(a, "b.{x}.d", regex=True)
    assert result == {}  # No match should return an empty dict

    a = {"b": {"c": {"d": 1}}}
    with pytest.raises(re.error):
        nested_getattr(a, "b.{[}.d", regex=True)

    # No attributes in leafs
    a = {"b": {"c": {"d": {}}, "e": {"f": {}}}}
    result = nested_getattr(a, "b.{.*}.{.*}.{.*}", regex=True)
    assert result == {}
    # But it did find the empty dicts
    result = nested_getattr(a, "b.{.*}.{.*}", regex=True)
    assert result == {"b.c.d": {}, "b.e.f": {}}
