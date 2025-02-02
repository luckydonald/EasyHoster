from abc import abstractmethod
from datetime import datetime
from enum import StrEnum
from typing import Literal, NewType, TypedDict, cast as hint, Annotated
from typing_extensions import Doc

from pydantic import BaseModel, Field

from .utils import now


class Role(StrEnum):
    ADMIN = "admin"
    NORMAL = "normal"
# end class


Roles = list[Role]

Username = NewType('Username', str)
Password = NewType('Password', str)


class ToFullInterface:
    @abstractmethod
    def to_full(self, *args, **kwargs) -> "FullUser":
        ...
    # end def
# end class


class SharedUserData(BaseModel, ToFullInterface):
    """
    Data both in the DB and in the API responses.
    """
    roles: Roles

    # noinspection PyMethodOverriding
    def to_full(
        self,
        username: Username,
        password: Password
    ) -> "FullUser":
        return FullUser(
            username=username,
            password=password,
            roles=self.roles,
        )
    # end def
# end class


class StoredUser(SharedUserData):
    password: Password
    # roles: see SharedUserData

    # noinspection PyMethodOverriding
    def to_full(
        self,
        username: Username,
    ) -> "FullUser":
        return FullUser(
            username=username,
            password=self.password,
            roles=self.roles,
        )
    # end def
# end class


StoredUsers = dict[Username, StoredUser]


class DatabaseV1(BaseModel):
    version: Literal[1] = 1
    users: StoredUsers
# end class


type DatabaseLatest = DatabaseV1



class ApiUser(SharedUserData):
    username: Username

    # noinspection PyMethodOverriding
    def to_full(
        self,
        password: Password
    ) -> "FullUser":
        return FullUser(
            username=self.username,
            password=password,
            roles=self.roles,
        )
    # end def
# end class


class FullUser(ApiUser, StoredUser, SharedUserData):
    pass
    # username: see ApiUser
    # password: see StoredUser
    # roles: see SharedUserData

    def to_api(self) -> ApiUser:
        return ApiUser(
            username=self.username,
            roles=self.roles,
        )
    # end def

    def to_stored(self) -> StoredUser:
        return StoredUser(
            password=self.password,
            roles=self.roles,
        )
    # end def

    # noinspection PyMethodOverriding
    def to_full(
        self,
    ) -> "FullUser":
        return self.model_copy()
    # end def
# end class


class Token(BaseModel):
    access_token: Annotated[str, Doc("The access token, jwt encoded & signed.")]
    token_type: str
# end class


class TokenData(BaseModel):
    username: str
    expires_at: datetime = Field(default_factory=now)
# end class

