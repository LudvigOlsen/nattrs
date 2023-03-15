nattrs
--------

Nested attributes utility functions for python. Allows getting/setting of object attributes and dict members interchangeably.
Useful to populate nested dicts for storing outputs of a loop.

Alpha stage. Subject to change.

> https://pypi.python.org/pypi/nattrs/     

> $ pip install nattrs  
> $ python -m pip install git+https://github.com/ludvigolsen/nattrs

Update this package but not dependencies:
> $ python -m pip install --force-reinstall --no-deps git+https://github.com/ludvigolsen/nattrs

| Class/Function   | Description |
|:-----------------|:------------|
| `nested_getattr` | Get object attributes/dict members recursively, given by dot-separated names |
| `nested_setattr` | Set object attribute/dict member by recursive lookup, given by dot-separated names. |
| `nested_mutattr` | Apply function (mutate) to object attribute/dict member by recursive lookup, given by dot-separated names. |
| `nested_hasattr` | Check whether recursive object attributes/dict members exist. |


# Examples

Create class `B` with a dict `c` with the member `d`:

```python

class B:
    def __init__(self):
        self.c = {
            "d": 1
        }

```

Add to a dict `a`:

```python

a = {"b": B()}

```

## nested_getattr

Get the value of `d`:

```python

nested_getattr(a, "b.c.d")
>> 1

```

Get default value when not finding an attribute:

```python

nested_getattr(a, "b.o.p", default="not found")
>> "not found"

```

## nested_setattr

Set the value of `d`:

```python

nested_setattr(a, "b.c.d", 2)

```

Check new value of `d`:

```python

nested_getattr(a, "b.c.d")
>> 2

```

## nested_mutattr

Mutate `d` with an anonymous function (lambda):

```python

nested_mutattr(a, "b.c.d", lambda x: x * 5)

```

Check new value of `d`:

```python

nested_getattr(a, "b.c.d")
>> 10

```

## nested_hasattr

Check presence of the member 'd':

```python

nested_hasattr(a, "b.c.d")
>> True

```

Fail to find member 'o':

```python

nested_hasattr(a, "b.o.p")
>> False

```