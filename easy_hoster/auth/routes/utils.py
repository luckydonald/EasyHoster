from fastapi import APIRouter
from starlette import status

from ..crypt import hash_password
from ..depends import AuthenticatedAdmin, AuthenticatedNormal
from ..depends import AuthenticatedUser
from ..models import ApiUser, Password

utils = APIRouter()
@utils.get("/test/normal")
async def foobar(current_user: AuthenticatedNormal):
    return {"message": "Foobar for normal users", "user": current_user}
# end def


@utils.get("/test/admin")
async def foobar(current_user: AuthenticatedAdmin):
    return {"message": "Foobar for admin users", "user": current_user}
# end def


@utils.get("/me", response_model=ApiUser, status_code=status.HTTP_201_CREATED)
async def read_users_me(current_user: AuthenticatedUser):
    return current_user.to_api()
# end def


@utils.post("/hash_password")
async def login(password: Password):
    """ Helper route to hash a password, for manually putting it to the database/json config."""
    return {"hash": hash_password(password)}
# end def

