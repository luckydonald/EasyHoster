from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .models import FullUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


Token = Annotated[str, Depends(oauth2_scheme)]

OAuthPasswordForm = Annotated[OAuth2PasswordRequestForm, Depends()]

from .core import get_current_user
AuthenticatedUser = Annotated[FullUser, Depends(get_current_user)]
