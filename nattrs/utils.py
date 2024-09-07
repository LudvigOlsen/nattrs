from dataclasses import dataclass
import re
from typing import Dict, List, Tuple, Any
from collections.abc import Mapping, MutableMapping

DOT_PLACEHOLDER = "[[DOT]]"  # Placeholder for dots inside regex terms


def get_or_make_attr(__o: object, __name: str):
    if not hasattr(__o, __name):
        setattr(__o, __name, {})
    return getattr(__o, __name)


def dict_getter(obj: Mapping, key: Any, default: Any):
    if isinstance(default, str):
        if default == "raise":
            return obj[key]
        if default == "make":
            if key not in obj:
                obj[key] = {}
                return obj[key]
    return obj.get(key, default)


def dict_setter(obj: MutableMapping, key: Any, val: Any):
    obj[key] = val


def dict_has(obj: Mapping, key: Any):
    return key in obj


def replace_dots_in_regex(attr: str) -> str:
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


def precompile_regexes(terms: List[str]) -> Tuple[str, Dict[str, re.Pattern]]:
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


def extract_terms(attr: str):
    return [
        term.replace(DOT_PLACEHOLDER, ".")
        for term in replace_dots_in_regex(attr).split(".")
    ]


class Ignore:
    """
    Class for indicating that a value
    should be ignored.

    Example
    -------
    >>> if isinstance(x, Ignore):
    >>>     continue

    or

    >>> l = [1, 2, Ignore(), 4]
    >>> for el in l:
    >>>     if not isinstance(el, Ignore):
    >>>         print(el)

    """

    pass


@dataclass(frozen=True)
class MatchResult:
    __slots__ = ["attr_name", "value"]
    attr_name: str
    value: Any


class MissingAttr:
    pass


def get_class_attributes(obj):
    """Return only user-defined attributes, excluding methods and built-in attributes."""
    if hasattr(obj, "__dict__"):
        return obj.__dict__.keys()
    return []


def flatten_matches(lst):
    for item in lst:
        if isinstance(item, list):
            yield from flatten_matches(item)
        else:
            yield item
