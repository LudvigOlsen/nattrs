from typing import Callable, Union, Any
from collections.abc import Mapping
from nattrs.setter import nested_setattr
from nattrs.getter import nested_getattr
from nattrs.utils import Ignore


def nested_mutattr(
    obj: Union[object, Mapping],
    attr: str,
    fn: Callable,
    is_inplace_fn: bool = False,
    getter_default: Any = Ignore(),
    regex: bool = False,
) -> None:
    r"""
    Mutate object attribute / dict member by recursive lookup, given by dot-separated names.

    Pass `attr='x.a.o'` to mutate attribute "o" of attribute "a" of attribute "x".

    When the attribute doesn't exist, we either ignore the attribute
    (when `getter_default = Ignore()` (default)) or pass the user-specified
    `getter_default` value to the mutating `fn` and create the missing
    attribute.

    Tip: The mutating function can perform checks of typing (e.g., consistency between
    the new and original values) or similar.

    Note: When the attributes / keys in `attr` themselves include dots, those need to be
    matched with regex patterns (see `regex`).

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to mutate an attribute/member of a sub-attribute/member of.
        These work interchangeably, why "class, dict, class, ..." work as well.
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
        E.g., useful for `numpy.ndarrays` that we do not
        wish to copy.
        Note: Since no value is directly assigned to `obj`,
        this cannot be done on `getter_default` values
        for missing attributes.
    getter_default : Any
        The value to use for attributes that weren't found.
        Either:
            `Ignore()` (default)
                Leads to no action being taken on those missing attributes.
            User-specified value (e.g., `None`)
                This value is passed to `fn()` and the attribute is created
                with the returned value (note: `is_inplace_fn=True` won't work
                in this case as the value would never be assigned to `obj`).
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. When multiple matches exist, they all
        get mutated.

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

    Using regex to find attribute names / dict keys:

    >>> nested_mutattr(a, "b.{.*}.d", lambda x: x * 5, regex=True)

    Check new value of d:

    >>> nested_getattr(a, "b.c.d")
    50  # (i.e. 10 * 5)
    """
    if regex:
        _regex_nested_mutattrs(
            obj=obj,
            attr=attr,
            fn=fn,
            is_inplace_fn=is_inplace_fn,
            getter_default=getter_default,
        )
    else:
        _nested_mutattr(
            obj=obj,
            attr=attr,
            fn=fn,
            is_inplace_fn=is_inplace_fn,
            getter_default=getter_default,
        )


def _nested_mutattr(
    obj: Union[object, Mapping],
    attr: str,
    fn: Callable,
    is_inplace_fn: bool,
    getter_default: Any,
) -> None:
    old_val = nested_getattr(
        obj=obj,
        attr=attr,
        default=getter_default,
    )
    if isinstance(old_val, Ignore):
        return
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


def _regex_nested_mutattrs(
    obj: Union[object, Mapping],
    attr: str,
    fn: Callable,
    is_inplace_fn: bool,
    getter_default: Any,
) -> None:
    # Get existing values
    old_vals = nested_getattr(
        obj=obj,
        attr=attr,
        default=getter_default,
        regex=True,
    )

    old_vals = {
        path: old_val
        for path, old_val in old_vals.items()
        if not isinstance(old_val, Ignore)
    }

    try:
        # If the function works in-place
        # e.g., on dicts or objects
        if is_inplace_fn:
            for old_val in old_vals.values():
                fn(old_val)
        else:
            new_vals = {path: fn(old_val) for path, old_val in old_vals.items()}
    except Exception as e:
        raise RuntimeError(
            f"Failed to apply `fn` to the existing value at `{attr}`: {e}"
        )
    if not is_inplace_fn:
        for path, new_val in new_vals.items():
            nested_setattr(
                obj=obj,
                attr=path,
                value=new_val,
                regex="{" in path,
            )
