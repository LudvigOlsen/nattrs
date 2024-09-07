from typing import Any
import pytest

from nattrs.nested_attributes import (
    nested_getattr,
    nested_hasattr,
    nested_mutattr,
    nested_setattr,
)


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


def test_nested_getattr_regex_examples():
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


def test_nested_setattr_examples():
    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {"d": 1}

    # Add to a dict 'a'
    a = {"b": B()}

    # Set the value of 'd'
    nested_setattr(a, "b.c.d", 2)
    # Check new value of d
    assert nested_getattr(a, "b.c.d") == 2

    # Create dict for missing `e` dict key
    nested_setattr(a, "b.c.e.f", 10, make_missing=True)
    assert nested_getattr(a, "b.c.e.f") == 10

    # Create dict for missing `h` class attribute
    nested_setattr(a, "b.h.i", 7, make_missing=True)
    assert nested_getattr(a, "b.h.i") == 7


def test_nested_mutattr_examples():
    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {"d": 1}

    # Add to a dict 'a'
    a = {"b": B(), "o": {"n": [0, 1, 2, 3, 4, 5]}}

    # Set the value of 'd'
    nested_mutattr(a, "b.c.d", lambda x: x * 5)
    # Check new value of d
    assert nested_getattr(a, "b.c.d") == 5

    # Apply function to list of integers
    nested_mutattr(a, "o.n", lambda xs: [xi + 3 for xi in xs], is_inplace_fn=False)
    # Check new value of n
    assert nested_getattr(a, "o.n") == [3, 4, 5, 6, 7, 8]

    def change_dict(d: dict) -> None:
        d["p"] = [x + 1 for x in d["n"]]
        del d["n"]

    # Apply inplace function to dict
    nested_mutattr(a, "o", change_dict, is_inplace_fn=True)

    # Check new value of p
    assert list(nested_getattr(a, "o").keys()) == ["p"]
    assert nested_getattr(a, "o.p") == [4, 5, 6, 7, 8, 9]

    def handle_missing(x: Any):
        if isinstance(x, str) and x == "missing_value":
            return "missing"
        return x

    nested_mutattr(a, "b.c.h", handle_missing, getter_default="missing_value")
    assert nested_getattr(a, "b.c.h") == "missing"
