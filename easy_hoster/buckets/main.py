from pathlib import Path
from typing import NamedTuple

from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse
from uuid import UUID

import os
import uuid6
import shutil

from .depends import UploadedFile, Now
from .models import Bucket
from .models import FileMetadataWithBucket
from ..auth.depends import AuthenticatedAdmin

bucket = APIRouter()


# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")

# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


@bucket.post("/upload/{bucket}")
async def upload_file(
    bucket: Bucket,
    file: UploadedFile,
    user: AuthenticatedAdmin,
    now: Now,
):
    if not user:
        raise HTTPException(status_code=403, detail="Not authorized to upload files")
    # end if

    file_id = uuid6.uuid7()
    folder = UPLOAD_DIR / bucket
    folder.mkdir(exist_ok=True)
    file_location = folder / f"{file_id!s}.blob"
    meta_location = folder / f"{file_id!s}.meta"

    meta = FileMetadataWithBucket(
        bucket=bucket,
        file_id=file_id,
        original_name=file.filename,
        size=file.size,
        uploaded_by=user.username,
        uploaded_at=now,
        content_type=file.content_type,
        headers=file.headers,
    )
    with open(meta_location, "w") as f:
        data = object()
        data.foo = file.filename
        f.write(meta.model_dump_json())
    # end with
# end def


class GetFilePaths(NamedTuple):
    file: Path
    meta: Path
# end class


async def get_file_paths(
    bucket: Bucket,
    file_id: UUID,
) -> GetFilePaths:
    folder = UPLOAD_DIR / bucket
    file_location = folder / f"{file_id}.blob"
    meta_location = folder / f"{file_id}.meta"
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="File not found on disk")
    # end if
    if not os.path.exists(meta_location):
        raise HTTPException(status_code=404, detail="Metadata not found on disk")
    # end def
    return GetFilePaths(file_location, meta_location)
# end def


class GetFileMetadata(NamedTuple):
    file: Path
    meta: FileMetadataWithBucket
# end class


async def get_file_metadata(
    bucket: Bucket,
    file_id: UUID,
) -> GetFileMetadata:
    locations = await get_file_paths(bucket, file_id)
    with open(locations.meta) as f:
        data = f.read()
    # end with
    return GetFileMetadata(locations.file, data)
# end def


@bucket.get("/file/{bucket}/{file_id}")
async def get_file(
    file_id: UUID,
    bucket: Bucket,
    dl: bool = False,
):
    locations = await get_file_paths(bucket, file_id)
    if dl:
        return FileResponse(locations.file, media_type='application/octet-stream', filename=metadata_store[file_id].original_name)
    else:
        return FileResponse(locations.file)
    # end if
# end def


@bucket.get("/metadata/{bucket}/{file_id}")
async def get_metadata(
    file_id: UUID,
    bucket: Bucket,
    dl: bool = False,
):
    locations = await get_file_paths(bucket, file_id)
    if file_id not in metadata_store:
        raise HTTPException(status_code=404, detail="Metadata not found")
    # end if
    return metadata_store[file_id]
# end def