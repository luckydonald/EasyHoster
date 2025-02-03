from fastapi import APIRouter, HTTPException
from starlette import status

from .crypt import hash_password
from .depends import AuthenticatedAdmin
from .io import user_store
from .models import FullUser, Role, StoredUser, ApiUser

admin = APIRouter()


@admin.put("/users", response_model=FullUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    username: str,
    password: str,
    _: AuthenticatedAdmin,
    role: Role = Role.NORMAL,
):
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


@admin.post("/users", response_model=FullUser, status_code=status.HTTP_201_CREATED)
async def change_user(
    _: AuthenticatedAdmin,
    username: str,
    password: str | None = None,
    role: Role | None = None,
):
    if username not in user_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Username not found exists"
        )
    # end if

    # Note: This is not current_user, but the new one.
    user_to_change = user_store[username]

    if password is not None:
        hashed_password = hash_password(password)
        user_to_change.password = hashed_password
    # end if

    if role is not None:
        user_to_change.roles = [role]
    # end if

    user_store.save()

    return user_to_change
# end def


@admin.get("/users", response_model=list[ApiUser], status_code=status.HTTP_200_OK)
async def list_users(
    _: AuthenticatedAdmin,
):
    return [user.to_api() for user in user_store]
# end def
