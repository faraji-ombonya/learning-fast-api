from typing import Optional, Union

# simple types
def get_items(item_a: str, item_b: int, item_c: bool, item_d: bytes, item_e: float):
    return item_a, item_b, item_c, item_d, item_e

# Generic types with type parameters
def process_items(items: list[str]):
    for item in items:
        print(item)

# Tuple and Set
def process_other_items(items_t: tuple[int, int, str], items_s: set[bytes]):
    return items_t, items_s

# Dict
def process_other_items_again(items: dict[str, float]):
    for items_name, item_price in items.items():
        print(items_name)
        print(item_price)

# Union
# A variable can be of several types
def process_new_item(item: int | str):
    print(item)

def process_new_item_again(item: Union[int, str]):
    print(item)

# Possibly
# could also be None

# this is confusing
# despite keyword Optional, you can not call the function without passing name
def say_hi(name: Optional[str] = None):
    if name is not None:
        print(f"Hey {name}!")
    else:
        print("Hello world!")

# this is explicit, name can be string or None
def say_hi_again(name: Union[str, None]):
    if name is not None:
        print(f"Hey {name}!")
    else:
        print("Hello world!")

# this is the best approach with python 3.10+
def say_hi_once_more(name: str | None):
    if name is not None:
        print(f"Hey {name}")
    else:
        print("Hello world!")

# Generic Types
# Types that take type paramaters in square brackets
# e.g. list, tuple, set, dict, 

# Classes as types

class Person:
    def __init__(self, name: str):
        self.name = name

def get_person_name(one_person: Person):
    return one_person.name
