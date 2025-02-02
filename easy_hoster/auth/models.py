from pydantic import BaseModel, TypeAdapter
from typing import Literal


Role = Literal["admin", "normal"]
Roles = list[Role]

type Username = str

class UserCreate(BaseModel):
    username: Username
    password: str
    roles: Roles
# end class


class User(BaseModel):
    username: Username
    roles: Roles
# end class

class StoredUser(BaseModel):
    password: str
    roles: Roles

StoredUsers = dict[Username, StoredUser]

StoredUsersAdapter = TypeAdapter[StoredUsers](StoredUsers)
