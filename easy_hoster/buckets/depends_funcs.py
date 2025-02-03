__all__ = (
    'now',
    'current_user_has_effective_role',
    'current_user_has_effective_role_matching_meta',
)

from typing import Literal

from fastapi import HTTPException

from .paths import get_file_metadata
from ..auth.constants import CREDENTIALS_EXCEPTION
from ..auth.core import current_user_has_role, error_if_forbidden
from ..auth.depends import AuthenticatedUser, AuthenticatedUserOrNone
from ..auth.models import Role, FullUser
from ..auth.utils import now
from .models import EffectiveRole, Bucket, FileId


def current_user_has_effective_role(role: Role | EffectiveRole):
    async def _current_user_has_effective_role_uploader(current_user: AuthenticatedUser, bucket: Bucket, file_id: FileId):
        info = await get_file_metadata(bucket, file_id)
        return error_if_forbidden[AuthenticatedUser](
            allowed=current_user.username == info.meta.uploaded_by,
            role=role,
            user=current_user,
        )
    # end def

    async def _current_user_has_effective_role_unauthenticated(
        current_user: AuthenticatedUserOrNone,
    ) -> FullUser | None:
        return error_if_forbidden[FullUser | None](
            allowed=current_user is None,
            role=role,
            user=current_user,
        )
    # end def

    match role:
        case Role.ADMIN | Role.NORMAL:
            return current_user_has_role(role)
        # end case
        case EffectiveRole.UPLOADER:
            return _current_user_has_effective_role_uploader
        # end case
        case EffectiveRole.UNAUTHENTICATED:
            return _current_user_has_effective_role_unauthenticated
        # end case
        case default:
            raise ValueError(f"Invalid role: {role}")
        # end case
    # end match
# end def


async def current_user_has_effective_role_matching_meta(
    current_user: AuthenticatedUserOrNone,
    bucket: Bucket,
    file_id: FileId,
) -> FullUser | Literal[True] | None:
    info = await get_file_metadata(bucket, file_id)
    if current_user is None:
        if info.meta.allowed_roles.unauthenticated:
            return True
        # end if
        raise CREDENTIALS_EXCEPTION
    # end if

    for role, should_check in info.meta.allowed_roles:
        if not should_check:
            continue
        # end if
        func = current_user_has_effective_role(role)
        try:
            try:
                return await func(current_user=current_user, bucket=bucket, file_id=file_id)
            except TypeError:
                return await func(current_user=current_user)
            # end try
        except HTTPException:
            continue
        # end try
    # end for
    return None

