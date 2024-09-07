
# nattrs <a href='https://github.com/LudvigOlsen/nattrs'><img src='https://raw.githubusercontent.com/LudvigOlsen/nattrs/main/nattrs_242x280_259dpi.png' align="right" height="140" /></a>

**Nested attributes** utility functions for python. Allows getting/setting of object attributes and dict members interchangeably.
Useful to populate nested dicts for storing outputs of a loop.

The functions should work with most dict types (i.e. `Mapping` / `MutableMapping`) and classes.

Tip: Attribute names can be found using regular expressions.

> https://pypi.python.org/pypi/nattrs/     


# Installation

Install from PyPI:

```shell
pip install nattrs
```

Install from GitHub:

```shell
python -m pip install git+https://github.com/ludvigolsen/nattrs
```


# Main functions

| Class/Function     | Description                                                                         |
| :----------------- | :---------------------------------------------------------------------------------- |
| `nested_getattr`   | Get object attributes/dict members recursively, given by dot-separated names.       |
| `nested_setattr`   | Set object attribute/dict member by recursive lookup, given by dot-separated names. |
| `nested_mutattr`   | Apply function (mutate) to nested object attribute/dict member.                     |
| `nested_updattr`   | Update dict / class.__dict__ of nested attributes.                                  |
| `nested_hasattr`   | Check whether recursive object attributes/dict members exist.                       |
| `nested_delattr`   | Delete nested object attributes/dict members.                                       |
| `populate_product` | Create and populate nested dicts with specified layers and the same leaf value.     |


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

Note: If your function performs the assignment *in-place*, remember to enable the `is_inplace_fn` argument.

## nested_updattr

Update `d` with a dictionary:

```python

nested_updattr(a, "b.c.d", {"d": 3})

```

Check new value of `d`:

```python

nested_getattr(a, "b.c.d")
>> 3

```

Note: Also work on `class.__dict__` dicts.


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

## nested_delattr

Delete the member 'd':

```python

nested_delattr(a, "b.c.d")
nested_hasattr(a, "b.c.d")
>> False

```

Ignore that it fails to find member 'o':

```python

nested_delattr(a, "b.o.p", allow_missing=True)

```

## populate_product

In this example, we wish to pre-populate nested dicts with empty lists to allow appending within a `for` loop. First, we go through the manual approach of doing this. Second, we show how easy it is to do with `populate_product()`. 

Say we have 3 variables that can each hold 2 values. We want to compute *something* for each combination of these values. Let's first define these variables and their options:

```python

animal = ["cat", "dog"]
food = ["strawberry", "cucumber"]
temperature = ["cold", "warm"]

```

Let's generate the product of these options:

```python

import itertools

combinations = list(itertools.product(*[animal, food, temperature]))
combinations
>> [('cat', 'strawberry', 'cold'),
>>  ('cat', 'strawberry', 'warm'),
>>  ('cat', 'cucumber', 'cold'),
>>  ('cat', 'cucumber', 'warm'),
>>  ('dog', 'strawberry', 'cold'),
>>  ('dog', 'strawberry', 'warm'),
>>  ('dog', 'cucumber', 'cold'),
>>  ('dog', 'cucumber', 'warm')]

```

Now we can create a nested dict structure with a list in the leaf element:

```python

# Initialize empty dict
nested_dict = {}

for leaf in combinations:
    # Join each string with dot-separation:
    attr = ".".join(list(leaf))

    # Assign empty list to the leafs
    # `make_missing` creates dicts for each 
    # missing attribute/dict member
    nattrs.nested_setattr(
        obj=nested_dict,
        attr=attr,
        value=[],
        make_missing=True
    )

nested_dict
>> {'cat': {'strawberry': {'cold': [], 'warm': []},
>>          'cucumber':   {'cold': [], 'warm': []}},
>>  'dog': {'strawberry': {'cold': [], 'warm': []},
>>          'cucumber':   {'cold': [], 'warm': []}}}

```

This dict population is actually provided by `populate_product()`. Instead of an empty list, let's set the value to an "edibility" score that could be changed by a later function:

```python

layers = [animal, food, temperature]
populate_product(
    layers=layers,
    val=False
)
>> {'cat': {'strawberry': {'cold': False, 'warm': False},
>>          'cucumber':   {'cold': False, 'warm': False}},
>>  'dog': {'strawberry': {'cold': False, 'warm': False},
>>          'cucumber':   {'cold': False, 'warm': False}}}

```