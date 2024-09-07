import re
import pytest

from nattrs import nested_getattr, nested_setattr


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

    # From example
    nested_setattr(a, "b.{.*}.d", 5, regex=True)
    assert nested_getattr(a, "b.c.d")

    class C:
        def __init__(self):
            self.h = {"i": 5}

    a = {"b": {"c": C()}}
    nested_setattr(a, "b.c.h.i", 20)
    assert nested_getattr(a, "b.c.h.i") == 20

    a = {"x": {"y": {}}}
    nested_setattr(a, "x.y.z.q", 100, make_missing=True)
    assert nested_getattr(a, "x.y.z.q") == 100

    class D:
        def __init__(self):
            self.k = {"m": 2}

    a = {"l": D()}
    nested_setattr(a, "l.k.m", 30)
    assert nested_getattr(a, "l.k.m") == 30

    # KeyError for dicts
    a = {"b": {}}
    with pytest.raises(KeyError):
        nested_setattr(a, "b.non_existing.k", 50, make_missing=False)

    # AttributeError for class instances
    a = {"b": B()}
    with pytest.raises(AttributeError):
        nested_setattr(a, "b.e.d", "Never set", make_missing=False)

    # Negative tests

    # Should not affect other attributes
    a = {"b": {"c": {"d": 1, "e": 2}}}
    nested_setattr(a, "b.c.d", 50)
    assert a["b"]["c"]["d"] == 50
    assert a["b"]["c"]["e"] == 2  # Ensure "e" is unaffected

    # Setting nonexistent attributes with make_missing=False should not change the structure
    a = {"b": {"c": {"d": 1}}}
    a_orig = a.copy()
    try:
        nested_setattr(a, "b.nonexistent.c", 999, make_missing=False)
    except KeyError:
        pass
    assert a == a_orig
    assert "nonexistent" not in a["b"]  # Ensure "nonexistent" is not created
    assert a["b"]["c"]["d"] == 1  # Ensure "d" is unaffected


def test_nested_setattr_regex():
    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {"e": 1, "f": 3}
            self.d = {"e": 4, "g": 7}

    # Add to a dict 'a'
    a = {"b": B()}

    print("Using multiple regex:")
    nested_setattr(a, "b.{.*}.{.*}", 10, regex=True)

    print(nested_getattr(a, "b.{.*}.{.*}", regex=True))
    nested_getattr(a, "b.{.*}.{.*}", regex=True) == {
        "b.c.e": 10,
        "b.c.f": 10,
        "b.d.e": 10,
        "b.d.g": 10,
    }

    # Defaults to empty dict when nothing is found
    print("When nothing found, nothing changes:")
    nested_setattr(a, "b.o.{.*}.{.*}", value=80, make_missing=False, regex=True)
    print(nested_getattr(a, "b.{.*}.{.*}", regex=True))

    # object is None
    # assert nested_getattr(None, "b.o.{.*}", allow_none=True, regex=True) is None
    with pytest.raises(ValueError):
        assert nested_setattr(
            a, "b.o.{.*}.{.*}", value=80, make_missing=True, regex=True
        )

    print(nested_getattr(a, "b.{.*}.{.*}", regex=True))

    # Make missing works for non-regex terms
    nested_setattr(a, "b.{.*}.o", value=80, make_missing=True, regex=True)
    nested_getattr(a, "b.{.*}.0", regex=True) == {
        "b.c.o": 80,
        "b.d.o": 80,
    }

    # Cannot asign to an integer
    with pytest.raises(AttributeError):
        nested_setattr(a, "b.c.{.*}.o", value=80, make_missing=True, regex=True)

    a = {"b": {"c": {"d": 1}, "e": {"d": 2}}}
    nested_setattr(a, "b.{.*}.d", 50, regex=True)
    assert nested_getattr(a, "b.{.*}.d", regex=True) == {"b.c.d": 50, "b.e.d": 50}

    # Partial regex match for setting values
    a = {"b": {"c1": {"d": 1}, "c2": {"d": 2}}}
    nested_setattr(a, "b.{c1}.d", 60, regex=True)
    assert nested_getattr(a, "b.{.*}.d", regex=True) == {"b.c1.d": 60, "b.c2.d": 2}

    a = {"b": {"key1": {"d": 1}, "key2": {"d": 2}}}
    nested_setattr(a, "b.{key.*}.d", 60, regex=True)
    assert nested_getattr(a, "b.{key.*}.d", regex=True) == {
        "b.key1.d": 60,
        "b.key2.d": 60,
    }

    # Regex match for top-level keys
    a = {"data1": {"x": 1}, "data2": {"x": 2}}
    nested_setattr(a, "{data.*}.x", 100, regex=True)
    assert nested_getattr(a, "{data.*}.x", regex=True) == {
        "data1.x": 100,
        "data2.x": 100,
    }

    # Regex match but only for leaf keys
    a = {"data": {"x1": 1, "y1": 2, "z1": 3}}
    nested_setattr(a, "data.{x1|z1}", 200, regex=True)
    assert nested_getattr(a, "data.{.*}", regex=True) == {
        "data.x1": 200,
        "data.z1": 200,
        "data.y1": 2,
    }

    a = {"b": {"c": {"d": 1}}}
    nested_setattr(a, "b.{.*}.x", 80, regex=True, make_missing=True)
    assert nested_getattr(a, "b.{.*}.x", regex=True) == {"b.c.x": 80}

    # Negative tests

    # Regex setting should not affect non-matching keys
    a = {"b": {"c": {"d": 1, "f": 3}, "g": {"d": 2}}}
    nested_setattr(a, "b.{.*}.d", 100, regex=True)
    assert a["b"]["c"]["d"] == 100
    assert a["b"]["g"]["d"] == 100
    assert a["b"]["c"]["f"] == 3  # Ensure "f" is unaffected

    # Regex does not match, no changes made to any part
    a = {"b": {"c": {"d": 1}, "e": {"f": 2}}}
    a_orig = a.copy()
    nested_setattr(a, "b.{x}.d", 100, regex=True)
    assert a == a_orig
    assert a["b"]["c"]["d"] == 1  # No change, as regex didn't match
    assert a["b"]["e"]["f"] == 2  # Ensure "e.f" is unaffected

    a = {"b": {"c": {"d": 1}, "e": {"f": 2}}}
    a_orig = a.copy()
    try:
        nested_setattr(a, "b.{[}.d", 100, regex=True)
    except re.error:
        pass
    assert a == a_orig
    assert a["b"]["c"]["d"] == 1  # Ensure no change on invalid regex
    assert a["b"]["e"]["f"] == 2  # Ensure "e.f" is unaffected
