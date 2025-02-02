__all__ = (
    'now',
    'current_user_has_effective_role',
    'current_user_has_effective_role_matching_meta',
)

from fastapi import HTTPException

from .paths import get_file_metadata
from ..auth.core import current_user_has_role, error_if_forbidden
from ..auth.depends import AuthenticatedUser, AuthenticatedUserOrNone
from ..auth.models import Role, FullUser
from ..auth.utils import now
from .models import EffectiveRole, Bucket, FileId


def current_user_has_effective_role(role: Role | EffectiveRole):
    async def _current_user_has_effective_role_uploader(current_user: AuthenticatedUser, bucket: Bucket, file_id: FileId):
        info = await get_file_metadata(bucket, file_id)
        return error_if_forbidden(
            allowed=current_user.username == info.meta.uploaded_by,
            role=role,
            user=current_user,
        )
    # end def

    async def _current_user_has_effective_role_unauthenticated(
        current_user: AuthenticatedUserOrNone,
    ) -> FullUser:
        return error_if_forbidden(
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
    current_user: AuthenticatedUser,
    bucket: Bucket,
    file_id: FileId,
) -> FullUser | None:
    info = await get_file_metadata(bucket, file_id)

    for role in info.meta.allowed_roles:#
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

