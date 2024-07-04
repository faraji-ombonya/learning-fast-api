from datetime import datetime

from pydantic import BaseModel, PositiveInt

class User(BaseModel):
    id: int
    name: str = "Jonh Doe"
    signup_ts: datetime | None = None
    friends: list[int] = []

external_data = {
    "id":"123",
    "signup_ts": "2024-06-01 22:40",
    "friends": [1, "2", b"3"],
}

user = User(**external_data)

print(user)
print(user.id)
