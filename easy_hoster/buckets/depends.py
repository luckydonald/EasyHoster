__all__ = (
    "UploadedFile",
    "Now",
)

from datetime import datetime
from typing import Annotated

from fastapi import UploadFile, File, Depends

from .depends_funcs import now, current_user_has_effective_role
from .models import EffectiveRole
from ..auth.models import Role, FullUser

UploadedFile = Annotated[UploadFile, File(description="A file read as UploadFile")]

Now = Annotated[datetime, Depends(now)]

# noinspection PyPep8Naming
def AuthenticatedUserWithEffectiveRole(role: Role | EffectiveRole):
    return Annotated[FullUser, Depends(current_user_has_effective_role(role))]
# end def

AuthenticatedUploader = AuthenticatedUserWithEffectiveRole(EffectiveRole.UPLOADER)
AuthenticatedUnauthenticated = AuthenticatedUserWithEffectiveRole(EffectiveRole.UNAUTHENTICATED)
