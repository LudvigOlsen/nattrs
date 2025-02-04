import re
import pytest

from nattrs.getter import nested_getattr
from nattrs.updater import nested_updattr


def test_nested_updattr():
    # Test 1: Update an existing dict attribute
    a = {"b": {"c": {"d": 1, "e": 2}}}
    nested_updattr(a, "b.c", {"e": 20, "f": 30})
    assert nested_getattr(a, "b.c") == {"d": 1, "e": 20, "f": 30}

    # Test 2: Update a non-dict attribute should raise TypeError
    a = {"b": {"c": 1}}
    with pytest.raises(TypeError) as exc_info:
        nested_updattr(a, "b.c", {"e": 20})
    assert "is not a dict or an object with a __dict__" in exc_info.value.args[0]

    # Test 2B: Update a non-dict attribute should raise TypeError
    a = {"b": {"c": 1}}
    with pytest.raises(TypeError) as exc_info:
        nested_updattr(a, "d.c", {"e": 20})
    assert "is not a dict or an object with a __dict__" in exc_info.value.args[0]

    # Test 2C: Update a non-dict attribute should raise TypeError
    a = {"b": {"c": 1}}
    with pytest.raises(TypeError) as exc_info:
        nested_updattr(a, "{.*}.c", {"e": 20}, regex=True)
    assert "is not a dict or an object with a __dict__" in exc_info.value.args[0]

    # Test 3: Update a class attribute's __dict__
    class B:
        def __init__(self):
            self.d = 1
            self.e = 2

    a = {"b": B()}
    nested_updattr(a, "b", {"e": 20, "f": 30})
    assert a["b"].__dict__ == {"d": 1, "e": 20, "f": 30}
    assert a["b"].f == 30

    # Test 4: Update with regex match
    a = {"b": {"c": {"d": 1}, "e": {"d": 2}}}
    nested_updattr(a, "b.{.*}", {"d": 10}, regex=True)
    assert nested_getattr(a, "b.{.*}.d", regex=True) == {"b.c.d": 10, "b.e.d": 10}
    # Update adds new value but doesn't change existing
    nested_updattr(a, "b.{.*}", {"h": 3.0}, regex=True)
    assert nested_getattr(a, "b.{.*}.h", regex=True) == {"b.c.h": 3.0, "b.e.h": 3.0}
    assert nested_getattr(a, "b.{.*}.d", regex=True) == {"b.c.d": 10, "b.e.d": 10}

    # Test 5: Update regex with no matches (should be ignored)
    a = {"b": {"c": {"d": 1}}}
    nested_updattr(a, "b.{.*}.z", {"new_attr": 50}, regex=True)
    assert nested_getattr(a, "b.{.*}", regex=True) == {"b.c": {"d": 1}}

    # Test 6: Update with regex across multiple levels
    a = {"b": {"c1": {"d": 1}, "c2": {"d": 2}}}
    nested_updattr(a, "b.{c.*}", {"new_key": 100}, regex=True)
    assert nested_getattr(a, "b.c1.new_key") == 100
    assert nested_getattr(a, "b.c2.new_key") == 100
    assert nested_getattr(a, "b.{.*}.new_key", regex=True) == {
        "b.c1.new_key": 100,
        "b.c2.new_key": 100,
    }

    # Test 7: Update on empty dict with regex
    a = {"b": {"c": {}}}
    nested_updattr(a, "b.c", {"new_key": 100}, regex=False)
    assert nested_getattr(a, "b.c.new_key") == 100

    # Test 8: Update on non-existent attribute with regex, should be ignored
    a = {"b": {"c": {"d": 1}}}
    nested_updattr(a, "b.{x.*}", {"new_key": 100}, regex=True)
    assert nested_getattr(a, "b.c.d") == 1  # Unchanged

    # Test 9: Trying to update a non-dict, non-class attribute
    a = {"b": {"c": 1}}
    with pytest.raises(TypeError):
        nested_updattr(a, "b.c", {"new_key": 100})

    # Test 10: Trying to update a non-existent path with regex=False
    a = {"b": {"c": {"d": 1}}}
    with pytest.raises(TypeError):
        nested_updattr(a, "b.nonexistent", {"new_key": 100}, regex=False)
    assert "new_key" not in a["b"]  # Ensure no update occurs

    # Test 11: Invalid regex pattern
    a = {"b": {"c": {"d": 1}}}
    with pytest.raises(re.error):
        nested_updattr(a, "b.{[}.d", {"new_key": 100}, regex=True)

    # Test 12: Trying to update a class instance without a __dict__
    class NoDictClass:
        __slots__ = ["attr"]

    a = {"b": NoDictClass()}
    with pytest.raises(TypeError) as exc_info:
        nested_updattr(a, "b", {"new_attr": 100})
    assert "is not a dict or an object with a __dict__" in exc_info.value.args[0]

    # Test 13: Trying to update using regex where no matches are found
    a = {"b": {"c": {"d": 1}}}
    nested_updattr(a, "b.{x.*}", {"new_key": 100}, regex=True)
    assert "new_key" not in a["b"]["c"]  # Ensure no update occurs

    # Test 14: Attempting to update a non-dict attribute within a class
    class TestClass:
        def __init__(self):
            self.value = 10  # Not a dict

    a = {"b": TestClass()}
    with pytest.raises(TypeError):
        nested_updattr(a, "b.value", {"new_key": 100})

    # Test 15: Updating with a non-dict update_dict
    a = {"b": {"c": {"d": 1}}}
    with pytest.raises(TypeError) as exc_info:
        nested_updattr(a, "b.c", "not a dict")
    assert (
        "`update_dict` must be of type `Mapping` (e.g., `dict`) but was"
        in exc_info.value.args[0]
    )

    # Test 16: Updating an attribute where intermediate path is missing
    a = {"b": {}}
    with pytest.raises(TypeError):
        nested_updattr(a, "b.c.d", {"new_key": 100})
