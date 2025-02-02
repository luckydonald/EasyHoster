from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from .core import get_current_user
from .models import FullUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


Token = Annotated[str, Depends(oauth2_scheme)]

AuthenticatedUser = Annotated[FullUser, Depends(get_current_user)]
