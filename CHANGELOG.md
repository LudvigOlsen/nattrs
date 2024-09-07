Changelog
--------

v0.1.xx (xx-2024)

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