from typing import Any
import pytest

from nattrs import nested_getattr, nested_mutattr, Ignore


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


def test_nested_mutattr_without_regex():
    class B:
        def __init__(self):
            self.c = {"d": 1, "e": 2, "q": [1]}

    a = {"b": B()}

    # Test 0: Mutate nonexistent attribute without alternative default
    # Ignores it and does not create a problem
    nested_mutattr(a, "b.c.f", lambda x: x + 3)
    assert nested_getattr(a, "b.c.f", default="MISSING") == "MISSING"

    # Test 1: Mutate existing attribute
    nested_mutattr(a, "b.c.d", lambda x: x * 5)
    assert nested_getattr(a, "b.c.d") == 5

    # Test 2: Mutate another attribute
    nested_mutattr(a, "b.c.e", lambda x: x + 10)
    assert nested_getattr(a, "b.c.e") == 12

    # Test 3: Mutate with an inplace function
    def app(x):
        if isinstance(x, list):
            x.append(30)
        return None

    nested_mutattr(
        a,
        "b.c.q",
        fn=app,
        is_inplace_fn=True,
        getter_default=[],
    )
    assert nested_getattr(a, "b.c.q") == [1, 30]

    # Test 4: Mutate nonexistent attribute with default
    nested_mutattr(a, "b.c.f", lambda x: 99 if x is None else x, getter_default=None)
    assert nested_getattr(a, "b.c.f") == 99

    # Test 6: Mutate deep nested attribute
    a["b"].c["h"] = {"i": 10}
    nested_mutattr(a, "b.c.h.i", lambda x: x + 5)
    assert nested_getattr(a, "b.c.h.i") == 15

    # Test 7: Fail to mutate a non-existing attribute with getter_default=10
    nested_mutattr(a, "b.c.nonexistent", lambda x: x + 50, getter_default=10)
    # A new attribute should be created with the value 60
    assert nested_getattr(a, "b.c.nonexistent") == 60

    # Test 8: Mutate a nonexistent key without getter_default, should create it
    nested_mutattr(a, "b.c.k", lambda x: 100 if x is None else x, getter_default=None)
    assert nested_getattr(a, "b.c.k") == 100

    # Test 9: Nested object mutation
    nested_mutattr(a, "b.c.h", lambda x: x.update({"i": 20}), is_inplace_fn=True)
    assert nested_getattr(a, "b.c.h.i") == 20


def test_nested_mutattr_with_regex():
    class B:
        def __init__(self):
            self.c = {"d": 1, "e": 2}
            self.f = {"g": 10, "h": 20, "o": [20]}

    a = {"b": B()}

    # Test 11: Mutate multiple attributes using regex
    nested_mutattr(a, "b.{.*}.d", lambda x: x + 5, regex=True)
    assert nested_getattr(a, "b.{.*}.d", regex=True, default=Ignore()) == {"b.c.d": 6}

    # Test 12: Mutate multiple existing and non-existent values with regex
    nested_mutattr(a, "b.{.*}.g", lambda x: x * 2, regex=True)
    assert nested_getattr(a, "b.{.*}.g", regex=True, default=Ignore()) == {"b.f.g": 20}
    nested_mutattr(a, "b.{.*}.g", lambda x: x * 2, getter_default=5, regex=True)
    assert nested_getattr(a, "b.{.*}.g", default=Ignore(), regex=True) == {
        "b.f.g": 40,  # already 20 at this point
        "b.c.g": 10,  # Was created as 5 and mutated
    }

    # Test 13: Inplace mutation with regex
    nested_mutattr(
        a,
        "b.{.*}.o",
        lambda x: x.append(99),
        is_inplace_fn=True,
        regex=True,
    )
    assert nested_getattr(a, "b.{.*}.o", default=Ignore(), regex=True) == {
        "b.f.o": [20, 99]
    }

    # Test 14: Mutate with default value when regex matches no attribute
    nested_mutattr(
        a,
        "b.{.*}.nonexistent",
        lambda x: 50 if x is None else x,
        regex=True,
        getter_default=None,
    )
    assert nested_getattr(a, "b.{.*}.nonexistent", regex=True) == {
        "b.c.nonexistent": 50,
        "b.f.nonexistent": 50,
    }

    # Test 15: Multiple regex matches with default
    nested_mutattr(a, "b.{.*}.newattr", lambda x: 99, getter_default=None, regex=True)
    assert nested_getattr(a, "b.{.*}.newattr", regex=True) == {
        "b.c.newattr": 99,
        "b.f.newattr": 99,
    }

    # Test 16: Regex match with deep nesting
    a["b"].c["nested"] = {"key": 5, "other": 10}
    nested_mutattr(a, "b.c.nested.{key|other}", lambda x: x * 2, regex=True)
    assert nested_getattr(a, "b.c.nested.{.*}", regex=True) == {
        "b.c.nested.key": 10,
        "b.c.nested.other": 20,
    }

    # Test 17: Creates no_match with fn(default) -> 0
    nested_mutattr(
        a,
        "b.{.*}.nomatch",
        lambda x: x + 1 if x is not None else 0,
        regex=True,
        getter_default=None,
    )
    assert nested_getattr(a, "b.{.*}.nomatch", regex=True) == {
        "b.c.nomatch": 0,
        "b.f.nomatch": 0,
    }

    # Test 17B: Ignore no_match attributes
    nested_mutattr(
        a,
        "b.{.*}.nononomatch",
        lambda x: x + 1 if x is not None else 0,
        regex=True,
    )
    assert nested_getattr(a, "b.{.*}.nononomatch", default="missing", regex=True) == {
        "b.c.nononomatch": "missing",
        "b.f.nononomatch": "missing",
    }

    # Test 18: Mutate regex match with mixed data types
    a["b"].c["mixed"] = [1, 2, 3]
    nested_mutattr(
        a, "b.{.*}.mixed", lambda x: x.append(4), is_inplace_fn=True, regex=True
    )
    assert nested_getattr(a, "b.{.*}.mixed", default=Ignore(), regex=True) == {
        "b.c.mixed": [1, 2, 3, 4]
    }

    # Test 19: Ensure regex mutation doesn't affect unrelated attributes
    a["b"].unrelated = {"x": 100}
    nested_mutattr(a, "b.{.*}.d", lambda x: x + 1, regex=True)
    assert (
        nested_getattr(a, "b.unrelated.x") == 100
    )  # Unrelated attribute should not be affected
