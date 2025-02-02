from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from .core import get_current_user, is_admin
from .crypt import hash_password
from .depends import AuthenticatedAdmin, AuthenticatedNormal
from .depends import AuthenticatedUser
from .io import user_store
from .models import FullUser, StoredUser, Role, ApiUser, Password
from .oauth_password import oauth_password

auth = APIRouter()
auth.include_router(oauth_password)

@auth.post("/users", response_model=FullUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    username: str,
    password: str,
    current_user: AuthenticatedAdmin,
    role: Role = Role.NORMAL,
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

    # Note: This is not current_user, but the new one.
    new_user = StoredUser(
        password=hashed_password,
        roles=[role],
    )
    user_store[username] = new_user
    return new_user
# end def


@auth.get("/test/normal")
async def foobar(current_user: AuthenticatedNormal):
    return {"message": "Foobar for normal users", "user": current_user}
# end def


@auth.get("/test/admin")
async def foobar(current_user: AuthenticatedAdmin):
    return {"message": "Foobar for admin users", "user": current_user}
# end def


@auth.get("/me", response_model=ApiUser, status_code=status.HTTP_201_CREATED)
async def read_users_me(current_user: AuthenticatedUser):
    return current_user.to_api()
# end def


@auth.post("/hash_password")
async def login(password: Password):
    """ Helper route to hash a password, for manually putting it to the database/json config."""
    return {"hash": hash_password(password)}
# end def

