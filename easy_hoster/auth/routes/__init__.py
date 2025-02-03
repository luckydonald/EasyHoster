from fastapi import APIRouter

# the oauth_password needs to go first for circular import reasons.
from .oauth_password import oauth_password

from .users import users
from .utils import utils
from ..constants import OAUTH_ROUTE_PREFIX

auth = APIRouter()
auth.include_router(utils, prefix="/utils", tags=["utils"])
auth.include_router(oauth_password, prefix=OAUTH_ROUTE_PREFIX, tags=["oauth"])
auth.include_router(users, prefix="/users", tags=["users"])
