import os
import json
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from .io import user_store
from .models import User


from fastapi import APIRouter

auth = APIRouter()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    return pwd_context.hash(password)
# end def

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
# end def


def get_user(username: str) -> User | None:
    if username in user_store:
        return User(**user_store[username].model_dump(), username=username)
    else:
        return None
    # end if
# end def


def is_admin(user: User) -> bool:
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


@auth.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # end if
    return {"access_token": form_data.username, "token_type": "bearer"}
# end def


@auth.post("/users")
async def create_user(
    username: str,
    password: str,
    role: str = "normal",
    current_user: User = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create users"
        )
    # end if
    if username in user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    # end if
    hashed_password = get_password_hash(password)
    user_data[username] = {"password": hashed_password, "role": role}
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)
    # end with
    return {"username": username, "role": role}
# end def


@auth.get("/test/normal")
async def foobar(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "normal":
        return {"message": "Foobar for normal users"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only normal users can access this route"
        )
    # end if
# end def

@auth.get("/test/admin")
async def foobar(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "normal":
        return {"message": "Foobar for normal users"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only normal users can access this route"
        )
    # end if
# end def
