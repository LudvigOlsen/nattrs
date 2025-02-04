Changelog
--------

v0.2.3 (02-2025)

 - Updates pyproject.toml to new poetry version.

v0.2.2 (09-2024)

 - Fixes path to hexagon badge when viewing outside of GitHub.

v0.2.0 (09-2024)

 - Adds `nested_delattr()` for deleting attributes / dict members
   in nested data structures.
 - Adds `nested_updattr()` for updating dicts and `class.__dict__` of 
   nested attributes with a `dict`.
 - Adds `regex` argument to `nested_*attr()` functions for using 
   regular expression to index attribute names / dict keys.
 - Adds `getter_default` argument to `nested_mutattr()` to allow 
   better handling of missing attributes.
 - Adds `Ignore()` class to use as `default` value in `nested_getattr()`
   and `getter_default` in `nested_mutattr()`.
 - Removes mutability requirements from type hints when they are
   unnecessary (only the sub object/Mapping needs to by mutable).
 - Adds hexagon bagde.

v0.1.3 (09-2024)

 - Adds `__version__` variable to package.
 - Changes type hints from `dict` to `Mapping` and `MutableMapping` 
   since the functions should work for those in general. 

v0.1.2 (07-2024)
 - Handles `zipp` vulnerability.
 - Now requires `Python==3.8` or newer.

v0.1.1 (03-2023)
 - Reformats README

v0.1.0 (03-2023)
 - Sets up package with `poetry`.
 - Initial main functions are: 
    - `nested_getattr()`
    - `nested_hasattr()`
    - `nested_setattr()`
    - `nested_mutattr()`
    - `populate_product()`