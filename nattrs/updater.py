from collections.abc import Mapping
from typing import Dict, Union

from nattrs.mutator import nested_mutattr
from nattrs.utils import Ignore


def nested_updattr(
    obj: Union[object, Mapping],
    attr: str,
    update_dict: Dict,
    regex: bool = False,
) -> None:
    r"""
    Update object attribute / dict member by recursive lookup.

    Pass `attr='x.a.o'` to update the attribute "o" of attribute "a" of attribute "x".

    Note: When the attributes / keys in `attr` themselves include dots, those need to be
    matched with regex patterns (see `regex`).

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to update the attribute/member of.
    attr : str
        The string specifying the dot-separated names of attributes/members.
        When `regex=False`, the attribute must exist or an error is raised.
    update_dict : dict
        Dictionary containing the updates to apply to the target attribute.
        When updating a class instance (i.e. `.__dict__`), keys should be
        valid attribute names (strings with no whitespace etc.)
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. When multiple matches exist, they all
        get updated. Overall non-existing matches are ignored.

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
    """

    if not isinstance(update_dict, Mapping):
        raise TypeError(
            "`update_dict` must be of type `Mapping` (e.g., `dict`) "
            f"but was: {type(update_dict)}"
        )

    def update_fn(existing_value):
        if not isinstance(existing_value, dict):
            if hasattr(existing_value, "__dict__"):
                existing_value = existing_value.__dict__
            else:
                raise TypeError(
                    f"Attribute '{attr}' is not a dict or an object with a __dict__"
                )
        existing_value.update(update_dict)
        return existing_value

    # Use nested_mutattr to update the found dictionary
    try:
        nested_mutattr(
            obj=obj,
            attr=attr,
            fn=update_fn,
            is_inplace_fn=True,
            getter_default=Ignore() if regex else None,
            regex=regex,
        )
    except RuntimeError as e:
        if "is not a dict or an object with a __dict__" in str(e):
            raise TypeError(str(e).split(":")[1])
        if "dictionary update sequence element" in str(e):
            raise ValueError(str(e).split(":")[1])
        raise
    except Exception:
        raise
