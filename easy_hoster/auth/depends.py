__all__ = (
    "OAuthPasswordForm",
    "Token",
    "HasAuthenticatedUser",
    "AuthenticatedUser",
    "AuthenticatedUserOrNone",
    "AuthenticatedUserWithRole",
    "AuthenticatedAdmin",
    "AuthenticatedNormal",
)

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .constants import ROUTE_PREFIX, OAUTH_ROUTE_PREFIX
from .models import FullUser, Role

OAuthPasswordForm = Annotated[OAuth2PasswordRequestForm, Depends()]

from .routes.oauth_password import login, oauth_password
oauth2_token_url = f"{ROUTE_PREFIX}{OAUTH_ROUTE_PREFIX}{oauth_password.url_path_for(login.__name__)}"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=oauth2_token_url, auto_error=False)
Token = Annotated[str, Depends(oauth2_scheme)]

from .core import get_current_user, has_current_user, get_current_user_or_none

HasAuthenticatedUser = Annotated[bool, Depends(has_current_user)]
AuthenticatedUser = Annotated[FullUser, Depends(get_current_user)]
AuthenticatedUserOrNone = Annotated[FullUser, Depends(get_current_user_or_none)]


# noinspection PyPep8Naming
def AuthenticatedUserWithRole(role: Role):
    from .core import current_user_has_role
    return Annotated[FullUser, Depends(current_user_has_role(role))]
# end def

AuthenticatedAdmin = AuthenticatedUserWithRole(Role.ADMIN)
AuthenticatedNormal = AuthenticatedUserWithRole(Role.NORMAL)
