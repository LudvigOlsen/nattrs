from typing import Callable, Union, Any
from collections.abc import Mapping
from nattrs.setter import nested_setattr
from nattrs.getter import nested_getattr


def nested_mutattr(
    obj: Union[object, Mapping],
    attr: str,
    fn: Callable,
    is_inplace_fn: bool = False,
    getter_default: Any = None,
) -> None:
    """
    Mutate object attribute/dict member by recursive lookup, given by dot-separated names.

    Pass `attr='x.a.o'` to mutate attribute "o" of attribute "a" of attribute "x".

    When the attribute doesn't exist, the mutating `fn` will receive `None`
    by default (see `getter_default`).

    Tip: The mutating function can perform checks of typing (e.g. consistency between
    the new and original values) or similar.

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to mutate an attribute/member of a sub-attribute/member of.
        These work interchangeably, why "class, dict, class" work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members.
        The most left name is an attribute/dict member of `obj`
        which has the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on. The last name may be non-existent and is the name
        of the attribute/member to set.
    fn : Callable
        Function that gets existing attribute/key value and
        returns the new value to be assigned.
    is_inplace_fn : bool
        Whether `fn` affects the attribute inplace. In this case,
        no output is expected (and is ignored), as we expect the
        function to have made the relevant change when applied.
        E.g. useful for `numpy.ndarrays` that we do not
        wish to copy.
    getter_default : Any
        Value to pass to `fn()` when the attribute was not found.

    Examples
    --------

    Create class 'B' with a dict 'c' with the member 'd':

    >>> class B:
    >>>     def __init__(self):
    >>>         self.c = {
    >>>             "d": 1
    >>>         }

    Add to a dict 'a':

    >>> a = {"b": B()}

    Mutate `d` with a lambda:

    >>> nested_mutattr(a, "b.c.d", lambda x: x * 5)

    Check new value of d:

    >>> nested_getattr(a, "b.c.d")
    10
    """
    old_val = nested_getattr(
        obj=obj,
        attr=attr,
        default=getter_default,
    )
    try:
        if is_inplace_fn:
            fn(old_val)
        else:
            new_val = fn(old_val)
    except Exception as e:
        raise RuntimeError(
            f"Failed to apply `fn` to the existing value at `{attr}`: {e}"
        )
    if not is_inplace_fn:
        nested_setattr(obj=obj, attr=attr, value=new_val)
