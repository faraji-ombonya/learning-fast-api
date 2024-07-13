from typing import Annotated

# the first type parameter you pass to Annotated is the actual type
def say_hello(name: Annotated[str, "this is just metadata"]) -> str:
    return f"Hello {name}"
