from typing import Annotated

from fastapi import FastAPI, Path, Query

app = FastAPI()

@app.get("/items/{item_id}")
async def read_items(
    item_id: Annotated[int, Path(title="The ID of the item to get")],
    q: Annotated[str | None, Query(alias="item-query")] = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q":q})
    return results


# Number validations, greater than or equal
# item_id: Annotated[int, Path(title="The Id of the item to get", ge=1, le=1000)], q: str