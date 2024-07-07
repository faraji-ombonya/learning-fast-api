from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI()

@app.get("/items/")
async def return_items(q: str | None = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


# Additional Validation
@app.get("/items/")
async def read_items(q: Annotated[str | None, Query(min_length=10, max_length=50, pattern="^fixedquery$")] = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


# Query parameter list / multiple values
@app.get("/items_2/")
async def read_items_2(q: Annotated[list[str] | None, Query()] = None):
    query_items = {"q":q}
    return query_items

# with defaults
# async def read_items_2(q: Annotated[list[str] | None, Query()] = ["Foo", "Bar"]):

# can also use list directly instead of list[str]
# asynce def read_items(q: Annotated[list | None, Query()] = []])

# Declare more metadata

@app.get("/items/")
async def read_items(
    q: Annotated[
        str | None, 
        Query(
            title="Query String", 
            min_length=3,
            
            # add a description 
            description="This is a description",

            # alias a paramater
            alias="item-query",

            # deprecate a parameter
            deprecated=True,

            # exclude from openAPI
            include_in_schema=False,
        ),
    ] = None
):
    pass