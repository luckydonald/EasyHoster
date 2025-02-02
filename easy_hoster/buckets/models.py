from datetime import datetime
from pathlib import Path
from typing import Annotated, NamedTuple, Mapping

from starlette.datastructures import Headers
from typing_extensions import Doc
from uuid import UUID

from pydantic import BaseModel, Field

from ..auth.models import Username, AccessLevel

BUCKET_PATTERN = "^[a-zA-Z0-9_-]+$"

Bucket = Annotated[str, Doc("Where it's stored in"), Field(pattern=BUCKET_PATTERN)]
FileId = Annotated[UUID, Doc("The UUID of the file.")]


class EffectiveRole(Role):
    UPLOADER = "uploader"
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
# end class


# noinspection PyArgumentList
AccessLevel = TypedDict(
    "AccessLevel",
    (
        { str(hint(EffectiveRole, role).value) : bool for role in Role }
    ),
    total=True,
)


class FileMetadata(BaseModel):
    file_id: Annotated[FileId, Doc("The newly generated UUID file name. Might be a UUID7 format.")]
    original_name: Annotated[str | None, Doc("The original file name.")]
    size: Annotated[int | None, Doc("The size of the file in bytes.")]
    access_level: Annotated[AccessLevel, Doc("The access level of the file, based on the roles.")]
    uploaded_by: Username
    uploaded_at: datetime
    content_type: Annotated[str | None, Doc("The content type of the request, from the headers.")]
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
        )
    # end def

    # noinspection PyMethodOverriding
    def as_with_bucket(self) -> 'FileMetadataWithBucket':
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
