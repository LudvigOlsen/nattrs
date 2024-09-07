from .getter import nested_getattr
from .has_checker import nested_hasattr
from .setter import nested_setattr
from .mutator import nested_mutattr
from .populate import populate_product
from .utils import Ignore


def get_version():
    import importlib.metadata

    return importlib.metadata.version("nattrs")


__version__ = get_version()
