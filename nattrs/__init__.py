from .getter import nested_getattr
from .has_checker import nested_hasattr
from .setter import nested_setattr
from .mutator import nested_mutattr
from .deleter import nested_delattr
from .updater import nested_updattr
from .populate import populate_product
from .utils import Ignore


def get_version():
    import importlib.metadata

    return importlib.metadata.version("nattrs")


__version__ = get_version()
