import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from .io import user_store
from .models import FullUser, Role, ApiUser, Username

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password):
    return pwd_context.hash(password)
# end def

def verify_password(*, password, hash):
    return pwd_context.verify(password, hash)
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

def fake_decode_token(token) -> FullUser:
    return FullUser(
        username=Username(token + "_fakedecoded"),
        roles=[Role.ADMIN],
        password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",

    )
# end def


async def get_current_user(token: str = Depends(oauth2_scheme)) -> FullUser:
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

