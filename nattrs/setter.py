from functools import partial
from typing import Callable, Dict, List, Any, Optional, Union
from collections.abc import Mapping, MutableMapping
import nattrs.utils as utils
import re


def nested_setattr(
    obj: Union[object, Mapping],
    attr: str,
    value: Any,
    make_missing: bool = False,
    regex: bool = False,
) -> None:
    r"""
    Set object attribute / dict member by recursive lookup, given by dot-separated names.

    Pass `attr='x.a.o'` to set attribute "o" of attribute "a" of attribute "x".

    When `make_missing` is disabled, it requires all but the last attribute/member to already exist.

    If you want type-checking of existing values before assignment (or similar checks),
    consider using `nested_mutattr()` instead and include such checks in the mutator function.

    Note: When the attributes / keys in `attr` themselves include dots, those need to be
    matched with regex patterns (see `regex`).

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to set an attribute/member of a sub-attribute/member of.
        These work interchangeably, why "class, dict, class, ..." work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members.
        The most left name is an attribute/dict member of `obj`
        which has the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on. The last name can be non-existent and is the name
        of the attribute/member to set.
    value : Any
        Value to set for the final attribute/member.
    make_missing : bool
        Whether to create a dict for non-existent intermediate attributes/keys.
        Otherwise, the function will raise either an `AttributeError`
        or a `KeyError` based on the data structure.
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. When multiple matches exist, they all
        get the value assigned.

        Each regex matching is performed separately per attribute "level"
        (dot separated attribute name).

        Note: The entire attribute name must be included in the wrapper
        (i.e. the first and last character are "{" and "}"),
        otherwise the name is considered a "fixed" (non-regex)
        name. Dots within "{}" are respected (i.e. not considered path splits).

        Note that `make_missing` won't work on attribute names that are
        specified as regex patterns and will fail instead (what would
        be the key?). It will still work on the non-regex names.

        To include an attribute name in `attr` that itself contains a dot,
        use a regex like `r'{x\.y}'` (in context: `r'a.{x\.y}.c'`)
            Remember to escape the dots in the regex or they will
            be considered a regex symbol.


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

    Set the value of 'd':

    >>> nested_setattr(a, "b.c.d", 2)

    Check new value of 'd':

    >>> nested_getattr(a, "b.c.d")
    2

    Using regex to find attribute names / dict keys:

    >>> nested_setattr(a, "b.{.*}.d", 5, regex=True)

    Check new value of 'd':

    >>> nested_getattr(a, "b.c.d")
    5

    Set value if it exists or ignore error otherwise:
    >>> try:
    >>>     nested_setattr(a, "b.c.o", "Never set")
    >>> except ValueError:
    >>>     pass

    """

    if regex:
        terms = [
            a.replace(utils.DOT_PLACEHOLDER, ".")
            for a in utils.replace_dots_in_regex(attr).split(".")
        ]
        attr, regexes = utils.precompile_regexes(terms)
        _regex_nested_setattrs(
            objs=[obj],
            attr=attr,
            value=value,
            make_missing=make_missing,
            regexes=regexes,
        )
    else:
        _nested_setattr(
            obj=obj,
            attr=attr,
            value=value,
            make_missing=make_missing,
        )


def _nested_setattr(
    obj: Union[object, Mapping],
    attr: str,
    value: Any,
    make_missing: bool = False,
):
    getter = (
        partial(utils.dict_getter, default="make" if make_missing else "raise")
        if isinstance(obj, Mapping)
        else (utils.get_or_make_attr if make_missing else getattr)
    )

    try:
        left, right = attr.split(".", 1)
    except:  # noqa: E722
        setter = utils.dict_setter if isinstance(obj, MutableMapping) else setattr
        setter(obj, attr, value)
        return
    nested_setattr(
        obj=getter(obj, left),
        attr=right,
        value=value,
        make_missing=make_missing,
    )


def _regex_nested_setattrs(
    objs: List[Union[object, Mapping]],
    attr: str,
    value: Any,
    make_missing: bool,
    regexes: Dict[str, re.Pattern],
) -> None:
    """
    Recursively set attributes for regex-matched paths.
    """
    for obj in objs:
        _regex_nested_setattr(
            obj=obj,
            attr=attr,
            value=value,
            make_missing=make_missing,
            regexes=regexes,
        )


def _regex_nested_setattr(
    obj: Union[object, Mapping],
    attr: str,
    value: Any,
    make_missing: bool,
    regexes: Dict[str, re.Pattern],
) -> None:
    if isinstance(obj, utils.MatchResult):
        obj = obj.value
    if obj is None:
        return [None]

    getter = (
        partial(utils.dict_getter, default="make" if make_missing else "raise")
        if isinstance(obj, Mapping)
        else (
            utils.get_or_make_attr if make_missing else lambda x, y: getattr(x, y, None)
        )
    )

    try:
        left, right = attr.split(".", 1)
    except ValueError:
        setter = utils.dict_setter if isinstance(obj, MutableMapping) else setattr
        _match_and_set_attr(
            obj=obj,
            attr=attr,
            value=value,
            setter=setter,
            getter=getter,
            regexes=regexes,
            make_missing=make_missing,
            is_leaf=True,
        )
        return

    matches = _match_and_set_attr(
        obj=obj,
        attr=left,
        value=value,
        setter=None,
        getter=getter,
        regexes=regexes,
        make_missing=make_missing,
        is_leaf=False,
    )

    _regex_nested_setattrs(
        objs=matches,
        attr=right,
        value=value,
        make_missing=make_missing,
        regexes=regexes,
    )


def _match_and_set_attr(
    obj: Any,
    attr: str,
    value: Any,
    setter: Optional[Callable],
    getter: Callable,
    regexes: Dict[str, re.Pattern],
    make_missing: bool,
    is_leaf: bool,  # Control whether this is a leaf node
    prev_attr: str = "",
) -> List[Any]:
    matches = []

    if attr.startswith("{") and attr.endswith("}"):
        regex_id = attr[1:-1]  # Extract the regex pattern
        pattern = regexes[regex_id]
        keys = (
            obj.keys() if isinstance(obj, Mapping) else utils.get_class_attributes(obj)
        )

        for key in keys:
            if re.fullmatch(pattern, key):
                if is_leaf:  # Only set if this is the final (leaf) term
                    setter(obj, key, value)
                matches.append(
                    utils.MatchResult(
                        attr_name=f"{prev_attr}.{key}" if prev_attr else key,
                        value=getter(obj, key),
                    )
                )
        if make_missing and not matches:
            raise ValueError(
                f"No match was found for regex: '{str(pattern.pattern)}'. "
                f"`make_missing` not possible for regex patterns."
            )
        return matches if matches else [None]

    # For non-regex terms, and if it's a leaf, set the value
    if is_leaf:
        setter(obj, attr, value)

    return [
        utils.MatchResult(
            attr_name=f"{prev_attr}.{attr}" if prev_attr else attr,
            value=getter(obj, attr),
        )
    ]
