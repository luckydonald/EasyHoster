from pydantic import BaseModel, TypeAdapter
from typing import Literal


Role = Literal["admin", "normal"]
Roles = list[Role]

type Username = str


class StoredUser(BaseModel):
    password: str
    roles: Roles
# end class


StoredUsers = dict[Username, StoredUser]

StoredUsersAdapter = TypeAdapter[StoredUsers](StoredUsers)


class User(StoredUser):
    username: Username
    # password: see StoredUser
    # roles: see StoredUser
# end class
