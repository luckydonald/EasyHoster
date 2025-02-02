import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from .io import user_store
from .models import FullUser, Role, ApiUser, Username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    return pwd_context.hash(password)
# end def

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
# end def


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


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = get_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # end if
    return user
# end def

