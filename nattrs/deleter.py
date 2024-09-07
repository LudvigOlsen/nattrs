from typing import List, Mapping, Union

from nattrs import utils
from nattrs.getter import nested_getattr


def nested_delattr(
    obj: Union[object, Mapping],
    attr: str,
    regex: bool = False,
    allow_missing: bool = True,
) -> None:
    r"""
    Delete object attribute / dict member by recursive lookup, given by dot-separated names.

    Pass `attr='x.a.o'` to delete attribute "o" of attribute "a" of attribute "x".

    Note: When the attributes / keys in `attr` themselves include dots, those need to be
    matched with regex patterns (see `regex`).

    Parameters
    ----------
    obj : object (class instance) or dict-like
        The object/dict to delete an attribute/member of a sub-attribute/member of.
        These work interchangeably, why "class, dict, class, ..." work as well.
    attr : str
        The string specifying the dot-separated names of attributes/members.
        The most left name is an attribute/dict member of `obj`
        which has the attribute/key given by the second most left name,
        which has the attribute/key given by the third most left name,
        and so on. The last name is the one to be deleted.
    regex : bool
        Whether to interpret attribute/member names wrapped in `{}`
        as regex patterns. When multiple matches exist, they all
        get deleted.

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

    allow_missing : bool
        Whether to silently skip deletion if the attribute/key does not exist.
        If `False`, a `KeyError` or `AttributeError` will be raised if not found.
        Note: This also silently returns when `obj` is `None`.

    Examples
    --------

    Create class 'B' with a dict 'c' with the member 'd':

    >>> class B:
    >>>     def __init__(self):
    >>>         self.c = {
    >>>             "d": 1,
    >>>             "e": 2,
    >>>         }

    Add to a dict 'a':

    >>> a = {"b": B()}

    Delete the member 'd':

    >>> nested_delattr(a, "b.c.d")

    Check remaining attributes:

    >>> nested_getattr(a, "b.c") == {"e": 2}
    """
    # If obj itself is None, handle it early
    if obj is None:
        if not allow_missing:
            raise AttributeError("`obj` was `None`. Cannot delete from `None` object")
        return
    if regex:
        # Get existing values for regex matching
        matched_vals = nested_getattr(
            obj=obj,
            attr=attr,
            regex=True,
            default=utils.Ignore(),  # Using the "Ignore" sentinel to avoid creating missing values
        )
        for path in matched_vals.keys():
            _regex_nested_delattrs(obj=obj, attr_terms=utils.extract_terms(path))
    else:
        try:
            _nested_delattr(obj=obj, attr=attr, allow_missing=allow_missing)
        except AttributeError as e:
            raise AttributeError("Attribute was not found: ", str(e))
        except KeyError as e:
            raise KeyError("Key was not found: ", str(e))
        except Exception:
            raise


def _nested_delattr(
    obj: Union[object, Mapping],
    attr: str,
    allow_missing: bool = True,
) -> None:
    getter = utils.dict_getter if isinstance(obj, Mapping) else getattr
    try:
        left, right = attr.split(".", 1)
    except ValueError:
        # Final deletion step
        if isinstance(obj, Mapping):
            if allow_missing and attr not in obj:
                return
            del obj[attr]
        else:
            if allow_missing and not hasattr(obj, attr):
                return
            delattr(obj, attr)
        return

    # Get the next attribute level
    next_obj = getter(obj, left, None)
    if obj is None:
        if not allow_missing:
            raise AttributeError(f"nested_delattr(): Attribute ({left}) not found.")
        return  # Early exit if allow_missing=True and next level doesn't exist

    # Recurse to the next level
    _nested_delattr(
        obj=next_obj,
        attr=right,
        allow_missing=allow_missing,
    )


def _regex_nested_delattrs(
    obj: Union[object, Mapping],
    attr_terms: List[str],
    allow_missing: bool = True,
) -> None:
    # No actual regexes at this point,
    # it's just the one for the regex

    # Get left term and remove the
    left_term = attr_terms[0]

    # If nested_getattr() made the attribute
    # into a regex with {} wrapper and escaping of dots
    # we clean it up for fixed lookup
    if left_term.startswith("{") and left_term.endswith("}"):
        left_term = left_term[1:-1].replace(r"\.", ".")

    getter = utils.dict_getter if isinstance(obj, Mapping) else getattr
    if len(attr_terms) > 1:
        right_terms = attr_terms[1:]
    else:
        # Final deletion step
        if isinstance(obj, Mapping):
            if allow_missing and left_term not in obj:
                return
            del obj[left_term]
        else:
            if allow_missing and not hasattr(obj, left_term):
                return
            delattr(obj, left_term)
        return

    # Get the next attribute level
    next_obj = getter(obj, left_term, None)
    if obj is None:
        if not allow_missing:
            raise AttributeError(
                f"nested_delattr(): Attribute ({left_term}) not found."
            )
        return  # Early exit if allow_missing=True and next level doesn't exist

    # Recurse to the next level
    _regex_nested_delattrs(
        obj=next_obj,
        attr_terms=right_terms,
        allow_missing=allow_missing,
    )
