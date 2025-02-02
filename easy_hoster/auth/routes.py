from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from .core import get_user, get_current_user, is_admin
from .crypt import hash_password, verify_password
from .depends import AuthenticatedUser
from .io import user_store
from .models import FullUser, StoredUser, Role, ApiUser

auth = APIRouter()


@auth.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(password=form_data.password, hash=user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # end if
    return {"access_token": form_data.username, "token_type": "bearer"}
# end def


@auth.post("/users", response_model=FullUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    username: str,
    password: str,
    role: Role = Role.NORMAL,
    current_user: FullUser = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create users"
        )
    # end if
    if username in user_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    # end if
    hashed_password = hash_password(password)

    new_user = StoredUser(
        password=hashed_password,
        roles=[role],
    )
    user_store[username] = new_user
    return new_user
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

@auth.get("/me", response_model=ApiUser, status_code=status.HTTP_201_CREATED)
async def read_users_me(current_user: AuthenticatedUser):
    return current_user.to_api()
# end def
