
# TODO Add more extensive testing

from nattrs.populate import populate_product

def test_populate_product_basic_usage():

    animal = ["cat", "dog"]
    food = ["strawberry", "cucumber"]
    temperature = ["cold", "warm"]
    layers = [animal, food, temperature]

    nested_dict = populate_product(
        layers=layers, 
        val=False
    )
    assert nested_dict == {
        'cat': {'strawberry': {'cold': False, 'warm': False},
                'cucumber':   {'cold': False, 'warm': False}},
        'dog': {'strawberry': {'cold': False, 'warm': False},
                'cucumber':   {'cold': False, 'warm': False}}}