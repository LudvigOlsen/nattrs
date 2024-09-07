from typing import Union
from collections.abc import Mapping
import nattrs.utils as utils


def nested_hasattr(obj: Union[object, Mapping], attr: str, allow_none: bool = False):
    """
    Check whether recursive object attributes/dict members exist.

    Pass `attr='x.a.o'` to check attribute "o" of attribute "a" of attribute "x".

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to check attributes/members of.
        These work interchangeably, why "class, dict, class" work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members
        to get. The most left name is the object/dict which has
        the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on.
    allow_none : bool
        Whether to allow `obj` to be `None` (in the first call - non-recursively).
        When allowed, such a call would return `False`.

    Returns
    -------
    bool
        Whether the final attribute/dict member exist.

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

    Check presence of the member 'd':

    >>> nested_hasattr(a, "b.c.d")
    True

    Fail to find member 'o':

    >>> nested_hasattr(a, "b.o.p")
    False
    """
    if not allow_none and obj is None:
        raise TypeError("`obj` was `None`.")
    return _nested_hasattr(obj=obj, attr=attr)


def _nested_hasattr(obj: Union[object, Mapping], attr: str):
    if obj is None:
        return False
    getter = utils.dict_getter if isinstance(obj, Mapping) else getattr
    has_checker = utils.dict_has if isinstance(obj, Mapping) else hasattr
    try:
        left, right = attr.split(".", 1)
    except:  # noqa: E722
        return has_checker(obj, attr)
    return _nested_hasattr(getter(obj, left, None), right)
