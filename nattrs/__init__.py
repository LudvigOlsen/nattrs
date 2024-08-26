from .nested_attributes import (
    nested_getattr,
    nested_hasattr,
    nested_setattr,
    nested_mutattr,
)
from .populate import populate_product


def get_version():
    import importlib.metadata

    return importlib.metadata.version("nattrs")


__version__ = get_version()
