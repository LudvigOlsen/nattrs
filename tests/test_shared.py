import pytest  # noqa: F401

from nattrs.deleter import nested_delattr
from nattrs.getter import nested_getattr
from nattrs.mutator import nested_mutattr
from nattrs.setter import nested_setattr
from nattrs.updater import nested_updattr


def test_nested_functions_with_dots_in_keys():
    # Test nested_getattr with dots in key
    a = {"b": {"c.special": {"d": 1}, "e": {"d": 2}}}
    result = nested_getattr(a, r"b.{c\.special}.d", regex=True)
    assert result == {r"b.{c\.special}.d": 1}

    # Test nested_setattr with dots in key
    a = {"b": {"c.special": {"d": 1}, "e": {"d": 2}}}
    nested_setattr(a, r"b.{c\.special}.d", 5, regex=True)
    assert nested_getattr(a, r"b.{c\.special}.d", regex=True) == {
        r"b.{c\.special}.d": 5
    }

    # Test nested_mutattr with dots in key
    a = {"b": {"c.special": {"d": 5}}}
    nested_mutattr(a, r"b.{c\.special}.d", lambda x: x + 5, regex=True)
    assert nested_getattr(a, r"b.{c\.special}.d", regex=True) == {
        r"b.{c\.special}.d": 10
    }

    # Test nested_updattr with dots in key
    a = {"b": {"c.special": {"d": 10}}}
    nested_updattr(a, r"b.{c\.special}", {"new_key": 20}, regex=True)
    assert nested_getattr(a, r"b.{c\.special}.new_key", regex=True) == {
        r"b.{c\.special}.new_key": 20
    }

    # Test nested_delattr with dots in key
    a = {"b": {"c.special": {"d": 1}, "e": {"d": 2}}}
    nested_delattr(a, r"b.{c\.special}.d", regex=True)
    assert "d" not in a["b"]["c.special"]
