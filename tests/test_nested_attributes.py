
import pytest

from nattrs.nested_attributes import nested_getattr, nested_hasattr, nested_mutattr, nested_setattr


def test_nested_getattr_examples():

    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {
                "d": 1
            }
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


def test_nested_hasattr_examples():

    # Create class 'B' with a dict 'c' with the member 'd'
    class B:
        def __init__(self):
            self.c = {
                "d": 1
            }
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
            self.c = {
                "d": 1
            }
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
            self.c = {
                "d": 1
            }
    # Add to a dict 'a'
    a = {
        "b": B(),
        "o": {"n": [0, 1, 2, 3, 4, 5]}
    }

    # Set the value of 'd'
    nested_mutattr(a, "b.c.d", lambda x: x * 5)
    # Check new value of d
    assert nested_getattr(a, "b.c.d") == 5

    # Apply function to list of integers
    nested_mutattr(
        a, "o.n", lambda xs: [xi + 3 for xi in xs],
        is_inplace_fn=False
    )
    # Check new value of n
    assert nested_getattr(a, "o.n") == [3, 4, 5, 6, 7, 8]

    def change_dict(d:dict) -> None:
        d["p"] = [x+1 for x in d["n"]]
        del d["n"]

    # Apply inplace function to dict
    nested_mutattr(
        a, "o", change_dict,
        is_inplace_fn=False
    )

    # Check new value of p
    assert list(nested_getattr(a, "o").keys()) == ["p"]
    assert nested_getattr(a, "o.p") == [4, 5, 6, 7, 8, 9]
