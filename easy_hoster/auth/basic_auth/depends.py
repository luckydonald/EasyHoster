__all__ = (
    "AuthenticatedUser",
    "AuthenticatedUserOrNone",
    "AuthenticatedUserWithRole",
    "AuthenticatedAdmin",
    "AuthenticatedNormal",
)

from typing import Annotated

from fastapi import Depends

from .core import authenticate_user, get_current_user_or_none
from ..models import FullUser, Role

# HasAuthenticatedUser = Annotated[bool, Depends(authenticate_user)]
AuthenticatedUser = Annotated[FullUser, Depends(authenticate_user)]
AuthenticatedUserOrNone = Annotated[FullUser | None, Depends(get_current_user_or_none)]


# noinspection PyPep8Naming
def AuthenticatedUserWithRole(role: Role):
    from .core import current_user_has_role
    return Annotated[FullUser, Depends(current_user_has_role(role))]
# end def

AuthenticatedAdmin = AuthenticatedUserWithRole(Role.ADMIN)
AuthenticatedNormal = AuthenticatedUserWithRole(Role.NORMAL)
