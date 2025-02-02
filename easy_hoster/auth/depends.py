from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .constants import ROUTE_PREFIX
from .models import FullUser

OAuthPasswordForm = Annotated[OAuth2PasswordRequestForm, Depends()]


from .oauth_password import login, oauth_password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{ROUTE_PREFIX}{oauth_password.url_path_for(login.__name__)}")


Token = Annotated[str, Depends(oauth2_scheme)]

from .core import get_current_user
AuthenticatedUser = Annotated[FullUser, Depends(get_current_user)]
