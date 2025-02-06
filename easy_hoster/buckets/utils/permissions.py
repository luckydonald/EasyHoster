from ...auth.models import Role

from ..models import EffectiveRole, EffectiveRoleAdditions


def file_permissions(
    roles_of_file: list[Role | EffectiveRoleAdditions | EffectiveRole],
    is_dir: bool = False,
) -> str:
    """
    :returns: something like `"rwxr-xr-x"`
    """

    # executable flag for folders
    e = 'x' if is_dir else '-'

    world = f'---'
    if EffectiveRoleAdditions.UNAUTHENTICATED in roles_of_file:
        world = f'r-{e}'
    # end if
    group = f'---'
    if Role.ADMIN in roles_of_file:
        group = f'rw{e}'
    # end if
    user = f'---'
    if EffectiveRoleAdditions.UPLOADER in roles_of_file:
        user = f'rw{e}'
    # end if
    return f'{world}{group}{user}'
# end def
