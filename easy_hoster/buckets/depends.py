__all__ = (
    "UploadedFile",
    "Now",
    "AuthenticatedUserWithEffectiveRole",
    "AuthenticatedUploader",
    "AuthenticatedUnauthenticated",
    "AuthenticatedMatchesMeta",
)

import json
from datetime import datetime
from typing import Annotated

from fastapi import UploadFile, File, Depends, Form
from pydantic import TypeAdapter, BaseModel

from .depends_funcs import now, current_user_has_effective_role, current_user_has_effective_role_matching_meta
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

AuthenticatedMatchesMeta = Annotated[FullUser, Depends(current_user_has_effective_role_matching_meta)]


# noinspection PyPep8Naming
def FormField[Generic](generic: type[Generic], key: str | None = None):
    import inspect

    if isinstance(generic, type) and issubclass(generic, BaseModel):
        # use BaseModel(**data) constructor
        def parser(x: str):
            print(f'FormField.parser - x: {x!r}')
            assert isinstance(x, str)
            data = json.loads(x)
            print(f'FormField.parser - data: {data!r}')
            assert isinstance(data, dict)
            return generic(**data)
        # end def
    else:
        def parser(x: str):
            return TypeAdapter[Generic](generic).validate_strings(x)
        # end def
    # end def
    print(f'FormField - parser: {parser}')

    def inner(key: str, default: Generic | None = None):
        print(f'FormField.inner - key: {key!r}, default: {default!r}')

        async def depends(**all: dict):
            print(f'FormField.inner.depends - form: {all}')
            if key not in all:
                return default
            # end if
            return parser(all[key])
        # end def
        param = inspect.Parameter(
            key,
            inspect.Parameter.POSITIONAL_ONLY,
            default=default,
            annotation=Annotated[str, Form()],
        )
        sig = inspect.signature(depends)
        sig = sig.replace(parameters=[param])
        depends.__signature__ = sig  # type: ignore

        new_type = Annotated[generic, Depends(depends)]
        print(f'FormField.inner - new_type: {new_type}')
        return new_type
    # end def
    if key is not None:
        print(f'FormField - inner(key={key!r}): {inner}')
        return inner(key)
    # end if
    print(f'FormField - inner: {inner}')
    return inner
# end def
