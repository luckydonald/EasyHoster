from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import ValidationError

from .constants import CREDENTIALS_EXCEPTION
from .depends import Token
from .io import user_store
from .models import FullUser, Role, Username
from .token import parse_token_data


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def load_user(username: Username) -> FullUser | None:
    if username in user_store:
        return FullUser(**user_store[username].model_dump(), username=Username(username))
    else:
        return None
    # end if
# end def


def is_admin(user: FullUser) -> bool:
    return Role.ADMIN in user.roles
# end def


async def has_current_user(token: Token) -> bool:
    user = await get_current_user_or_none(token)
    return bool(user)
# end def


async def get_current_user_or_none(token: Token) -> FullUser | None:
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
    # end try
# end def


async def get_current_user(token: Token) -> FullUser:
    """
    :raises HTTPException: Unauthorized.
    """

    try:
        token_data = parse_token_data(token)
    except (InvalidTokenError, ValidationError):
        raise CREDENTIALS_EXCEPTION
    # end if
    if token_data.username is None:
        raise CREDENTIALS_EXCEPTION
    # end if
    user = load_user(username=token_data.username)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    # end if
    return user
# end def


def current_user_has_role(role: Role):
    from .depends import AuthenticatedUser

    async def _current_user_has_role(current_user: AuthenticatedUser) -> FullUser:
        return error_if_forbidden(
            allowed=role in current_user.roles,
            role=role,
            user=current_user,
        )
    # end def

    return _current_user_has_role
# end def


def error_if_forbidden(
    *,
    allowed: bool,
    role: Role,
    user: FullUser,
) -> FullUser:
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Only users with role {role.value} can access this route.",
        )
    # end if
    return user
# end def
