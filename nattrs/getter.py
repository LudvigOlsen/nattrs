import re
from typing import Callable, Dict, List, Optional, Union, Any
from collections.abc import Mapping
from nattrs.utils import Ignore
import nattrs.utils as utils


def nested_getattr(
    obj: Union[object, Mapping],
    attr: str,
    default: Any = None,
    allow_none: bool = False,
    regex: bool = False,
) -> Optional[Union[Any, Dict[str, Any]]]:
    r"""
    Get object attributes / dict members recursively, given by dot-separated names.

    Pass `attr='x.a.o'` to get attribute "o" of attribute "a" of attribute "x".

    Use regular expression to get all matching attribute paths.

    Note: When the attributes / keys in `attr` themselves include dots, those need to be
    matched with regex patterns (see `regex`).

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to get attributes/members of.
        These work interchangeably, why "class, dict, class, ..." work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members to get.
        The most left name is an attribute/dict member of `obj`
        which has the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on.
    default : Any
        Value to return when one or more of the attributes were not found.
        When `regex=True` and you don't want a value for the non-existent
        attributes, pass `default=nattrs.Ignore()` which will be excluded
        from the output. For `regex=False`, any value is simply returned.
    allow_none : bool
        Whether to allow `obj` to be `None` (in the first call - non-recursively).
        When allowed, such a call would return `None`.
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. When multiple matches exist, all are returned
        in a list.

        Each regex matching is performed separately per attribute "level"
        (dot separated attribute name).

        Note: The entire attribute name must be included in the wrapper
        (i.e. the first and last character are "{" and "}"),
        otherwise the name is considered a "fixed" (non-regex)
        name.  Dots within "{}" are respected (i.e. not considered path splits).

        To include an attribute name in `attr` that itself contains a dot,
        use a regex like `r'{x\.y}'` (in context: `r'a.{x\.y}.c'`)
            Remember to escape the dots in the regex or they will
            be considered a regex symbol.

    Returns
    -------
    Any or dict[str, Any] or `None`
        When `obj` is `None` and `allow_none` is `True`: `None`

        When `regex=False`: Any
            One of:
                - The value of the final attribute/dict member.
                - The default value

        When `regex=True`: Dict[str, Any]
            Dict mapping matching attribute paths to one of:
                - The respective value of the final attribute/dict member.
                - The default value (except `nattrs.Ignore()` which are excluded).

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

    Get the value of 'd':

    >>> nested_getattr(a, "b.c.d")
    1

    Get default value when not finding an attribute:

    >>> nested_getattr(a, "b.o.p", default="not found")
    "not found"

    Using regex to find attribute names / dict keys:

    >>> nested_getattr(a, "b.{.*}.{.*}", regex=True)
    {"b.c.d": 1}

    """
    if obj is None:
        if not allow_none:
            raise TypeError("`obj` was `None`.")
        return None

    # When regex-use is enabled
    if regex:
        # Extract terms for regex compilation
        terms = utils.extract_terms(attr)
        attr, regexes = utils.precompile_regexes(terms)
        matches = _regex_nested_getattrs(
            objs=[obj],
            attr=attr,
            regexes=regexes,
            default=utils.MissingAttr(),
        )

        def _replace_missing(val):
            if isinstance(val, utils.MissingAttr):
                return default
            return val

        return {
            match.attr_name: _replace_missing(match.value)
            for match in utils.flatten_matches(matches)
            if isinstance(match, utils.MatchResult)
            and not isinstance(_replace_missing(match.value), Ignore)
        }

    # Separate method for non-regex version (faster, simpler)
    return _nested_getattr(obj=obj, attr=attr, default=default)


def _nested_getattr(obj: Union[object, Mapping], attr: str, default: Any = None):
    if obj is None:
        return obj
    getter = utils.dict_getter if isinstance(obj, Mapping) else getattr
    try:
        left, right = attr.split(".", 1)
    except:  # noqa: E722
        return getter(obj, attr, default)
    return _nested_getattr(
        obj=getter(obj, left, default),
        attr=right,
        default=default,
    )


def _regex_nested_getattrs(
    objs: List[Union[object, Mapping]],
    attr: str,
    regexes: Dict[str, re.Pattern],
    default: Any,
):
    return [
        _regex_nested_getattr(
            obj=obj,
            attr=attr,
            regexes=regexes,
            default=default,
        )
        for obj in objs
    ]


def _regex_nested_getattr(
    obj: Union[object, Mapping],
    attr: str,
    regexes: Dict[str, re.Pattern],
    default: Any,
):
    prev_attr = ""
    if isinstance(obj, utils.MatchResult):
        prev_attr = obj.attr_name
        obj = obj.value
    if isinstance(obj, utils.MissingAttr):
        return [utils.MissingAttr()]
    if obj is None:
        return [None]

    getter = utils.dict_getter if isinstance(obj, Mapping) else getattr
    try:
        left, right = attr.split(".", 1)
    except:  # noqa: E722
        return _match_and_get_attr(
            obj=obj,
            attr=attr,
            getter=getter,
            regexes=regexes,
            default=default,
            prev_attr=prev_attr,
        )

    return _regex_nested_getattrs(
        _match_and_get_attr(
            obj=obj,
            attr=left,
            getter=getter,
            regexes=regexes,
            default=default,
            prev_attr=prev_attr,
        ),
        attr=right,
        regexes=regexes,
        default=default,
    )


def _match_and_get_attr(
    obj: Any,
    attr: str,
    getter: Callable,
    regexes: Dict[str, re.Pattern],
    default: Any,
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
                # Collect all matches
                matches.append(
                    utils.MatchResult(
                        attr_name=f"{prev_attr}.{_dotted_attr(key)}"
                        if prev_attr
                        else key,
                        value=getter(obj, key, default),
                    )
                )
        return (
            matches if matches else [default]
        )  # Return all matches, or default if no match

    # Fallback to non-regex case
    return [
        utils.MatchResult(
            attr_name=f"{prev_attr}.{_dotted_attr(attr)}" if prev_attr else attr,
            value=getter(obj, attr, default),
        )
    ]


def _dotted_attr(s):
    if "." in s:
        return "{" + s.replace(".", r"\.") + "}"
    return s
