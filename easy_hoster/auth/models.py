from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, TypeAdapter


class Role(StrEnum):
    ADMIN = "admin"
    NORMAL = "normal"
# end class


Roles = list[Role]

type Username = str


class StoredUser(BaseModel):
    password: str
    roles: Roles
# end class


StoredUsers = dict[Username, StoredUser]

StoredUsersAdapter = TypeAdapter[StoredUsers](StoredUsers)


class DatabaseV1():
    version: Literal[1] = 1
    users: StoredUsers
# end class


type DatabaseLatest = DatabaseV1


class User(StoredUser):
    username: Username
    # password: see StoredUser
    # roles: see StoredUser
# end class
