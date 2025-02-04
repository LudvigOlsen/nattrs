import itertools
from typing import List, Any

from nattrs.setter import nested_setattr

# TODO Improve documentation
# TODO What if keys have dots in them? This *could* actually be a feature allowing
# to have some layers not be part of the product - but must be described in docs?


def populate_product(layers: List[List[Any]], val: Any) -> dict:
    r"""
    Create and populate a dict with layers of dicts
    with all leafs having the same value (e.g., an empty list).

    The branches are the product of `layers` (see `itertools.product()`),
    so `layers=[["a", "b"], ["c", "d"]]` gives the following branches:
        `"a.c", "a.d", "b.c", "b.d"`.


    Parameters
    ----------
    layers : List of lists of dict keys
        Each sublist is a "layer" in the nested dicts.
        Each layer can have any positive number of dict keys (must be hashable).
    val : Any
        Value to set for all leafs.

    Returns
    -------
    dict (of dicts)
        Nested dictionaries with a branch for each combination from the product
        (see `itertools.product()`) of the `layers`. The leaf value
        is specified through `val`.

    Example
    -------

    Set layers:

    >>> animal = ["cat", "dog"]
    >>> food = ["strawberry", "cucumber"]
    >>> temperature = ["cold", "warm"]
    >>> layers = [animal, food, temperature]

    Create and populate dict with the value "edibility" value `False`:

    >>> populate_product(
    >>>     layers=layers,
    >>>     val=False
    >>> )
    {'cat': {'strawberry': {'cold': False, 'warm': False},
             'cucumber':   {'cold': False, 'warm': False}},
     'dog': {'strawberry': {'cold': False, 'warm': False},
             'cucumber':   {'cold': False, 'warm': False}}}

    """

    assert all(
        [len(layer) > 0 for layer in layers]
    ), "All layers must have a positive number of keys (list elements)."

    combinations = list(itertools.product(*layers))

    nested_dict = {}

    for leaf in combinations:
        # Join each string with dot-separation
        attr = ".".join(list(leaf))

        # Assign empty list to the leafs
        # `make_missing` creates dicts for each
        # missing attribute/dict member
        nested_setattr(
            obj=nested_dict,
            attr=attr,
            value=val,
            make_missing=True,
        )
    return nested_dict
