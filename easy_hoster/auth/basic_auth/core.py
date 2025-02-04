# Set up basic authentication
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status

from ..crypt import verify_password
from ..io import user_store
from ..models import FullUser, Role

security = HTTPBasic()

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Authenticate the user using basic authentication.
    """
    # Implement your own user authentication logic here
    # user = load_user(username=token_data.username)

    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

    if credentials.username not in user_store:
        raise exception
    # end if
    stored_user = user_store.get(credentials.username)
    user = stored_user.to_full(username=credentials.username)
    if not user:
        raise exception
    # end if
    if not verify_password(password=credentials.password, hash=user.password):
        raise exception
    # end if
    return user
# end def


async def get_current_user_or_none(credentials: HTTPBasicCredentials = Depends(security)) -> FullUser | None:
    try:
        return authenticate_user(credentials)
    except HTTPException:
        return None
    # end try
# end def


def current_user_has_role(role: Role):
    from ..core import current_user_has_role as current_user_has_role_original
    # credentials: HTTPBasicCredentials = Depends(security)
    _current_user_has_role_original = current_user_has_role_original(role)

    async def _current_user_has_role(current_user: Depends(get_current_user_or_none)) -> FullUser:
        return await _current_user_has_role_original(current_user)
    # end def

    return _current_user_has_role
# end def
