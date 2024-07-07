from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name":"FOO"}, {"item_name":"BAR"}, {"item_name":"BAZ"}]


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]


# optional parameters
@app.get("/items_2/{item_id}")
async def read_item_2(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q":q}
    return {"item_id": item_id}


# Query parameter type conversion
@app.get("/items_3/{item_id}")
async def read_item_3(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q":q})

    if not short:
        item.update(
            {"description": "This is an amazing item that has a very long description."}
        )
    
    return item


# multiple path and query params
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q":q})
    if not short:
        item.update(
            {"description":"This Item has a very long dsecription"}
        )
    return item


# Required query paramaters
@app.get("/items_4/{item_id}")
async def read_user_item_4(item_id: str, needy: str, skip: int = 0, limit: int | None = None):
    item = {"item_id": item_id, "needy": needy}
    return item



