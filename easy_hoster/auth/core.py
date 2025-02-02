from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer


from .depends import Token
from .io import user_store
from .models import FullUser, Role, Username, Password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(username: str) -> FullUser | None:
    if username in user_store:
        return FullUser(**user_store[username].model_dump(), username=Username(username))
    else:
        return None
    # end if
# end def


def is_admin(user: FullUser) -> bool:
    return "admin" in user.roles
# end def


def fake_decode_token(token) -> FullUser:
    return FullUser(
        username=Username(token + "_fakedecoded"),
        roles=[Role.ADMIN],
        password=Password("$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"),
    )
# end def


async def get_current_user(token: Token) -> FullUser:
    """
    :raises HTTPException: Unauthorized.
    """
    user = fake_decode_token(token)
    # user = get_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # end if
    return user
# end def


def current_user_has_role(role: Role):
    from .depends import AuthenticatedUser

    async def _current_user_has_role(current_user: AuthenticatedUser):
        if role in current_user.roles:
            return current_user
        # end if
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Only users with role {role.value} can access this route.",
        )
    # end def

    return _current_user_has_role
# end def
