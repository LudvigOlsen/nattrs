from typing import Union
from collections.abc import Mapping
from nattrs.getter import nested_getattr
import nattrs.utils as utils


def nested_hasattr(
    obj: Union[object, Mapping],
    attr: str,
    allow_none: bool = False,
    regex: bool = False,
):
    r"""
    Check whether recursive object attributes / dict members exist.

    Pass `attr='x.a.o'` to check attribute "o" of attribute "a" of attribute "x".

    Note: When the attributes / keys in `attr` themselves include dots, those need to be
    matched with regex patterns (see `regex`).

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to check attributes/members of.
        These work interchangeably, why "class, dict, class, ..." work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members
        to get. The most left name is the object/dict which has
        the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on.
    allow_none : bool
        Whether to allow `obj` to be `None` (in the first call - non-recursively).
        When allowed, such a call would return `False`.
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. If one or more matches exist,
        the function returns `True`, else `False`.
        Each regex matching is performed separately per attribute "level"
        (dot separated attribute name).

        Note: The entire attribute name must be included in the wrapper
        (i.e. the first and last character are "{" and "}"),
        otherwise the name is considered a "fixed" (non-regex)
        name. Dots within "{}" are respected (i.e. not considered path splits).

        To include an attribute name in `attr` that itself contains a dot,
        use a regex like `r'{x\.y}'` (in context: `r'a.{x\.y}.c'`)
            Remember to escape the dots in the regex or they will
            be considered a regex symbol.

        NOTE: When `regex=True`, it simply calls `nested_getattr(..., regex=True)`
        and returns whether anything was found. If you want the found
        attributes, use that directly.

    Returns
    -------
    bool
        Whether (one of) the final attribute/dict member(s) exist.

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

    Using regex to find attribute names / dict keys:

    >>> nested_hasattr(a, "b.{.*}.d", regex=True)
    True

    >>> nested_hasattr(a, "b.{.*}.r", regex=True)
    False
    """
    if not allow_none and obj is None:
        raise TypeError("`obj` was `None`.")
    if regex:
        matches = nested_getattr(
            obj,
            attr,
            default=utils.MissingAttr(),
            regex=True,
        )
        return bool(
            [m for m in matches.values() if not isinstance(m, utils.MissingAttr)]
        )

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
