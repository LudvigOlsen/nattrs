import pytest

from nattrs import (
    nested_delattr,
    nested_getattr,
    nested_hasattr,
    nested_mutattr,
    nested_updattr,
)


MODULE_VALUE = "original"


class Victim:
    def __init__(self):
        self.value = 1


@pytest.mark.parametrize(
    "operation",
    [
        lambda obj: nested_getattr(obj, "__init__.__globals__.MODULE_VALUE"),
        lambda obj: nested_hasattr(obj, "__init__.__globals__.MODULE_VALUE"),
        lambda obj: nested_delattr(obj, "__init__.__globals__.MODULE_VALUE"),
        lambda obj: nested_mutattr(
            obj,
            "__init__.__globals__",
            lambda value: value.clear(),
            is_inplace_fn=True,
        ),
        lambda obj: nested_updattr(
            obj,
            "__init__.__globals__",
            {"MODULE_VALUE": "changed"},
        ),
        lambda obj: nested_getattr(
            obj,
            "__init__.__globals__.MODULE_VALUE",
            regex=True,
        ),
    ],
)
def test_main_functions_reject_dunder_object_attributes(operation):
    with pytest.raises(ValueError, match="__init__"):
        operation(Victim())


def test_getter_regex_cannot_select_a_dunder_object_attribute():
    with pytest.raises(ValueError, match="__init__"):
        nested_getattr(Victim, "{__init__}.__globals__", regex=True)


def test_main_functions_allow_dunder_mapping_keys():
    value = {"__metadata__": {"value": 1}}
    assert nested_getattr(value, "__metadata__.value") == 1
    assert nested_hasattr(value, "__metadata__.value")
    nested_delattr(value, "__metadata__.value")
    assert value == {"__metadata__": {}}
