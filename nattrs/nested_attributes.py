"""
Functionality for performing recursive get/set/has/mutate/update
on nested classes and dictionaries (interchangeably).

"""

from dataclasses import dataclass
import re
from functools import partial
from typing import Callable, Dict, List, Optional, Tuple, Union, Any
from collections.abc import Mapping, MutableMapping

# TODO Add tests
# TODO What if keys have dots in them? Add escaping of dots somehow?
# TODO Could we allow indexing a list with integers?

# TODO Add recursive update, concatenate, etc. for trees of dicts/objects
# TODO Allow setting custom object instead of dict? Would require some thinking but could be done
# TODO Make nested_delattr
# TODO For getattr -> allow different default for leaf
# TODO: nested_update
# TODO: wildcard (*) or regex in path leading to bulk op
# TODO: For multiple regex matches, return a dict with path -> value?

DOT_PLACEHOLDER = "[[DOT]]"  # Placeholder for dots inside regex terms

#### Getter ####


def nested_getattr(
    obj: Union[object, Mapping],
    attr: str,
    default: Any = None,
    allow_none: bool = False,
    regex: bool = False,
) -> Optional[Union[Any, Dict[str, Any]]]:
    """
    Get object attributes/dict members recursively, given by dot-separated names.

    Pass `attr='x.a.o'` to get attribute "o" of attribute "a" of attribute "x".

    Use regular expression to get all matching attribute paths.

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to get attributes/members of.
        These work interchangeably, why "class, dict, class" work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members to get.
        The most left name is an attribute/dict member of `obj`
        which has the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on.
    default : Any
        Value to return when one or more of the attributes were not found.
        NOTE: ignored when `regex=True` in which case an empty dict is the default.
    allow_none : bool
        Whether to allow `obj` to be `None` (in the first call - non-recursively).
        When allowed, such a call would return `None`.
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. When multiple matches exist, all are returned
        in a list. Note: The entire attribute name must be included
        in the wrapper, otherwise the name is considered a "fixed" (non-regex)
        name. This means, "{" and "}" can be used within the regex.
        Dots within "{}" are respected (i.e. not considered path splits).

    Returns
    -------
    Any or dict[str, Any] or `None`
        When `obj` is `None` and `allow_none` is `True`: `None`

        When `regex=False`: Any
            One/more of:
                - The value of the final attribute/dict member.
                - The default value

        When `regex=True`: Dict[str, Any]
            Dict mapping matching attribute paths to the value of
            their final attribute/dict members.
            When no matches were found, an empty dict is returned.



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
        terms = [
            a.replace(DOT_PLACEHOLDER, ".")
            for a in _replace_dots_in_regex(attr).split(".")
        ]
        attr, regexes = _precompile_regexes(terms)
        matches = _regex_nested_getattrs(
            objs=[obj],
            attr=attr,
            regexes=regexes,
            default=None,
        )
        return {
            match.attr_name: match.value
            for match in _flatten_matches(matches)
            if isinstance(match, MatchResult)
        }

    # Separate method for non-regex version (faster, simpler)
    return _nested_getattr(obj=obj, attr=attr, default=default)


def _nested_getattr(obj: Union[object, Mapping], attr: str, default: Any = None):
    if obj is None:
        return obj
    getter = _dict_getter if isinstance(obj, Mapping) else getattr
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
    default: Any = None,
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
    default: Any = None,
):
    prev_attr = ""
    if isinstance(obj, MatchResult):
        prev_attr = obj.attr_name
        obj = obj.value
    if obj is None:
        return [None]

    getter = _dict_getter if isinstance(obj, Mapping) else getattr
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
        keys = obj.keys() if isinstance(obj, Mapping) else _get_class_attributes(obj)

        for key in keys:
            if re.fullmatch(pattern, key):
                # Collect all matches
                matches.append(
                    MatchResult(
                        attr_name=f"{prev_attr}.{key}" if prev_attr else key,
                        value=getter(obj, key, default),
                    )
                )
        return (
            matches if matches else [default]
        )  # Return all matches, or default if no match

    # Fallback to non-regex case
    return [
        MatchResult(
            attr_name=f"{prev_attr}.{attr}" if prev_attr else attr,
            value=getter(obj, attr, default),
        )
    ]


#### Has checker ####


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
    getter = _dict_getter if isinstance(obj, Mapping) else getattr
    has_checker = _dict_has if isinstance(obj, Mapping) else hasattr
    try:
        left, right = attr.split(".", 1)
    except:  # noqa: E722
        return has_checker(obj, attr)
    return _nested_hasattr(getter(obj, left, None), right)


#### Setter ####


def nested_setattr(
    obj: Union[object, Mapping],
    attr: str,
    value: Any,
    make_missing: bool = False,
) -> None:
    """
    Set object attribute/dict member by recursive lookup, given by dot-separated names.

    Pass `attr='x.a.o'` to set attribute "o" of attribute "a" of attribute "x".

    When `make_missing` is disabled, it requires all but the last attribute/member to already exist.

    If you want type-checking of existing values before assignment (or similar checks),
    consider using `nested_mutattr()` instead and include such checks in the mutator function.

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to set an attribute/member of a sub-attribute/member of.
        These work interchangeably, why "class, dict, class" work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members.
        The most left name is an attribute/dict member of `obj`
        which has the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on. The last name may be non-existent and is the name
        of the attribute/member to set.
    value : Any
        Value to set for the final attribute/member.
    make_missing : bool
        Whether to create a dict for non-existent intermediate attributes/keys.
        Otherwise, the function will raise an error.

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
    """

    getter = (
        partial(_dict_getter, default="make" if make_missing else "raise")
        if isinstance(obj, Mapping)
        else (get_or_make_attr if make_missing else getattr)
    )
    setter = _dict_setter if isinstance(obj, Mapping) else setattr
    try:
        left, right = attr.split(".", 1)
    except:  # noqa: E722
        setter(obj, attr, value)
        return
    nested_setattr(
        obj=getter(obj, left),
        attr=right,
        value=value,
        make_missing=make_missing,
    )


#### Mutator ####


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


#### Getter/Setter/Checker utils ####


def get_or_make_attr(__o: object, __name: str):
    if not hasattr(__o, __name):
        setattr(__o, __name, {})
    return getattr(__o, __name)


def _dict_getter(obj: Mapping, key: Any, default: Any):
    if isinstance(default, str):
        if default == "raise":
            return obj[key]
        if default == "make":
            if key not in obj:
                obj[key] = {}
                return obj[key]
    return obj.get(key, default)


def _dict_setter(obj: MutableMapping, key: Any, val: Any):
    obj[key] = val


def _dict_has(obj: Mapping, key: Any):
    return key in obj


def _replace_dots_in_regex(attr: str) -> str:
    """Replace dots inside regex terms (inside `{}`) with a placeholder."""
    result = []
    inside_regex = False

    for char in attr:
        if char == "{":
            inside_regex = True
        elif char == "}":
            inside_regex = False
        if char == "." and inside_regex:
            result.append(DOT_PLACEHOLDER)
        else:
            result.append(char)

    return "".join(result)


def _precompile_regexes(terms: List[str]) -> Tuple[str, Dict[str, re.Pattern]]:
    """
    Extract regex patterns wrapped in `{}` that cover entire attribute terms,
    compile them, and replace them with placeholders like `regex_0`, `regex_1`, etc.

    Parameters
    ----------
    terms : List[str]
        List of the attribute names/keys.

    Returns
    -------
    Tuple[str, List[re.Pattern]]
        - The modified dot-joined attribute string with regex placeholders.
        - List of compiled regexes.
    """
    regexes = {}
    new_terms = []

    for i, term in enumerate(terms):
        # Check if the term is completely wrapped in {}
        if term.startswith("{") and term.endswith("}"):
            # Compile the regex inside the curly braces
            pattern = term[1:-1]
            compiled_regex = re.compile(pattern)
            regexes[f"regex_{i}"] = compiled_regex
            # Replace the regex term with a placeholder like 'regex_0'
            new_terms.append("{" + f"regex_{i}" + "}")
        else:
            new_terms.append(term)

    # Join the terms back into a dot-separated path
    modified_attr = ".".join(new_terms)

    return modified_attr, regexes


@dataclass
class MatchResult:
    attr_name: str
    value: Any


def _get_class_attributes(obj):
    """Return only user-defined attributes, excluding methods and built-in attributes."""
    if hasattr(obj, "__dict__"):
        return obj.__dict__.keys()
    return []


def _flatten_matches(lst):
    for item in lst:
        if isinstance(item, list):
            yield from _flatten_matches(item)
        else:
            yield item
