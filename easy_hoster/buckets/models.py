from abc import abstractmethod
from datetime import datetime
from enum import StrEnum
from itertools import chain
from pathlib import Path
from typing import Annotated, NamedTuple, Mapping

from starlette.datastructures import Headers
from starlette.requests import Request
from typing_extensions import Doc
from pydantic import BaseModel, Field, create_model, HttpUrl

from .utils.new_uuids import UUID7
from .utils.urls import add_query
from ..auth.models import Username, Role
from ..utils import hint

BUCKET_PATTERN = "^[a-zA-Z0-9_-]+$"

Bucket = Annotated[str, Doc("Where it's stored in"), Field(pattern=BUCKET_PATTERN)]
FileId = Annotated[UUID7, Doc("The UUID of the file."), ]


class EffectiveRoleAdditions(StrEnum):
    UPLOADER = "uploader"
    UNAUTHENTICATED = "unauthenticated"
# end class


EffectiveRole = StrEnum('EffectiveRole', [(hint(StrEnum, i).name, hint(StrEnum, i).value) for i in chain(Role, EffectiveRoleAdditions)])


access_level_defaults: dict[EffectiveRole, bool] = {
    EffectiveRole.ADMIN: True,
    EffectiveRole.NORMAL: False,
    EffectiveRole.UPLOADER: True,
    EffectiveRole.UNAUTHENTICATED: False,
}

# noinspection PyArgumentList
AllowedRoles = create_model(
    "AccessLevel",
    __doc__="The allowed roles for this file.",
    **{
        # https://docs.pydantic.dev/2.10/api/base_model/#pydantic.create_model
        # <name> : (<type>, <default value>),
        # <name> : (<type>, <pydantic.Field(…)>), or
        # <name> : typing.Annotated[<type>, <pydantic.Field(…)>]
        str(hint(StrEnum, role).value) : (bool, Field(examples=[access_level_defaults.get(role, False)]))
        for role
        in EffectiveRole
    }
)


class BaseFileMetadata(BaseModel):
    file_id: Annotated[FileId, Doc("The newly generated UUID file name. Might be a UUID7 format.")]
    original_name: Annotated[str | None, Doc("The original file name.")]
    size: Annotated[int | None, Doc("The size of the file in bytes.")]
    allowed_roles: Annotated[AllowedRoles, Doc("The access level of the file, based on the roles.")]
    uploaded_by: Username
    uploaded_at: datetime
    content_type: Annotated[str | None, Doc("The content type of the request, from the headers.")]

    @abstractmethod
    def as_basic(self) -> 'FileMetadata':
        pass
    # end def

    @abstractmethod
    def as_with_bucket(self, *, bucket: Bucket) -> 'FileMetadataWithBucket':
        pass
    # end def

    @abstractmethod
    def as_api(
        self,
        *,
        request: Request,
    ) -> 'FileMetadataForApi':
        pass
    # end def
# end class


class FileMetadata(BaseFileMetadata):
    headers: Annotated[Mapping[str, str], Headers, Doc("The headers of the request."), Field(examples=[{"Content-Type": "image/jif"}])]

    def as_basic(self) -> 'FileMetadata':
        return self
    # end def

    def as_with_bucket(self, *, bucket: Bucket) -> 'FileMetadataWithBucket':
        return FileMetadataWithBucket(
            bucket=bucket,
            **self.model_dump()
        )
    # end def

    # noinspection PyMethodOverriding
    def as_api(
        self,
        *,
        request: Request,
        bucket: Bucket,
    ) -> 'FileMetadataForApi':
        return self.as_with_bucket(bucket=bucket).as_api(request=request)
    # end def
# end class


class FileMetadataWithBucket(FileMetadata):
    bucket: Bucket

    def as_basic(self) -> FileMetadata:
        return FileMetadata(
            file_id=self.file_id,
            original_name=self.original_name,
            size=self.size,
            uploaded_by=self.uploaded_by,
            uploaded_at=self.uploaded_at,
            content_type=self.content_type,
            headers=self.headers,
            allowed_roles=self.allowed_roles,
        )
    # end def

    # noinspection PyMethodOverriding
    def as_with_bucket(self) -> 'FileMetadataWithBucket':
        return self
    # end def

    # noinspection PyMethodOverriding
    def as_api(
        self,
        *,
        request: Request,
    ) -> 'FileMetadataForApi':
        from .routes import get_file
        return FileMetadataForApi(
            # inherit everything except headers
            **{
                k: v
                for k, v in self.model_dump().items()
                if k != "headers"
            },
            # add embed_link and download_link.
            **{
                k: add_query(request.url_for(get_file.__name__, file_id=self.file_id, bucket=self.bucket), dl=dl)
                for k, dl in (('embed_link', False), ('download_link', True),)
            }
        )
    # end def
# end class


class FileMetadataForApi(BaseFileMetadata):
    bucket: Bucket
    embed_link: HttpUrl
    download_link: HttpUrl

    def as_basic(self) -> FileMetadata:
        return self.as_with_bucket().as_basic()
    # end def

    def as_with_bucket(self) -> FileMetadataWithBucket:
        return FileMetadataWithBucket(
            **{
                k: v
                for k, v in self.model_dump().items()
                if k not in ("embed_link", "download_link")
            },
        )
    # end def

    # noinspection PyMethodOverriding
    def as_api(self) -> 'FileMetadataForApi':
        return self
    # end def
# end class


class GetFilePaths(NamedTuple):
    file: Path
    meta: Path
    bucket: Path
# end class


class GetFileMetadata(NamedTuple):
    locations: GetFilePaths
    meta: FileMetadata
# end class


class UploadFileResult(BaseModel):
    file_id: FileId
# end class
