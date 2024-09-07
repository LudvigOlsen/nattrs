from copy import deepcopy
import pytest

from nattrs.deleter import nested_delattr


def test_nested_delattr():
    # Test 1: Delete a simple dict attribute
    a = {"b": {"c": {"d": 1, "e": 2}}}
    nested_delattr(a, "b.c.d")
    assert "d" not in a["b"]["c"]

    # Test 2: Attempt to delete a non-existent key with allow_missing=True
    a = {"b": {"c": {"d": 1}}}
    nested_delattr(a, "b.c.nonexistent", allow_missing=True)
    assert "d" in a["b"]["c"]

    # Test 3: Attempt to delete a non-existent key with allow_missing=False
    a = {"b": {"c": {"d": 1}}}
    with pytest.raises(KeyError) as exc_info:
        nested_delattr(a, "b.c.nonexistent", allow_missing=False)
    assert "Key was not found" in exc_info.value.args[0]

    # Test 4: Delete a nested attribute in a class
    class B:
        def __init__(self):
            self.c = {"d": 1, "e": 2}

    a = {"b": B()}
    nested_delattr(a, "b.c.d")
    assert "d" not in a["b"].c

    # Test B: Attempt to delete a non-existent attribute with allow_missing=False
    a = {"b": B()}
    with pytest.raises(AttributeError) as exc_info:
        nested_delattr(a, "b.k", allow_missing=False)
    assert "Attribute was not found" in exc_info.value.args[0]
    assert "o" not in a["b"].c
    assert "d" in a["b"].c
    assert "e" in a["b"].c

    # Test 5: Delete using regex
    a = {"b": {"c": {"d": 1}, "e": {"d": 2}}}
    nested_delattr(a, "b.{.*}.d", regex=True)
    assert "d" not in a["b"]["c"]
    assert "d" not in a["b"]["e"]

    # Test 6: Deleting from None with allow_missing=True
    a = {"b": None}
    nested_delattr(a, "b.c.d", allow_missing=True)  # Should not raise an error

    # Test 7: Deleting from None with allow_missing=False
    a = {"b": None}
    with pytest.raises(AttributeError):
        nested_delattr(a, "b.c.d", allow_missing=False)

    # Test 8: Deleting a non-existent path with regex (ignored)
    a = {"b": {"c": {"d": 1}}}
    nested_delattr(a, "b.{.*}.z", regex=True)
    assert "d" in a["b"]["c"]  # Should not delete anything

    # Test 9: Deleting from a non-dict object with regex
    a = {"b": {"c": {"d": 1}, "e": {"d": 2}}}
    nested_delattr(a, "b.{c|e}.d", regex=True)
    assert "d" not in a["b"]["c"]
    assert "d" not in a["b"]["e"]

    # Test 10: Deleting a top-level attribute
    a = {"b": {"c": {"d": 1}}}
    nested_delattr(a, "b.c")
    assert "c" not in a["b"]

    # Test 11: Regex with empty braces (should not match anything)
    a = {"b": {"c": {"d": 1}, "e": {"d": 2}}}
    nested_delattr(a, "b.{}", regex=True)
    assert "d" in a["b"]["c"]  # Nothing should be deleted
    assert "d" in a["b"]["e"]

    # Test 13: Regex for non-matching patterns
    a = {"b": {"c": {"d": 1}, "e": {"d": 2}, "f": {"d": 3}}}
    a_orig = deepcopy(a)
    nested_delattr(a, "b.{g}.d", regex=True)
    a == a_orig
    assert "d" in a["b"]["c"]  # Nothing should be deleted
    assert "d" in a["b"]["e"]
    assert "d" in a["b"]["f"]

    # Test 15: Regex matching multiple levels
    a = {"b": {"c": {"d": {"e": 1}}, "f": {"d": {"g": 2}}}}
    nested_delattr(a, "b.{c|f}.d.{e|g}", regex=True)
    assert "e" not in a["b"]["c"]["d"]
    assert "g" not in a["b"]["f"]["d"]

    # Test 16: Regex with no valid matches and no error
    a = {"b": {"c": {"d": 1}}}
    nested_delattr(a, "b.{x}.d", regex=True)
    assert "d" in a["b"]["c"]  # Nothing should be deleted
