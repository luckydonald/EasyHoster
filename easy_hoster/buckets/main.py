from pathlib import Path
from typing import NamedTuple

from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse
from uuid import UUID

import os
import uuid6
import shutil

from .paths import UPLOAD_DIR, check_file_paths
from .depends import UploadedFile, Now
from .io import write_meta
from .models import Bucket
from .models import FileMetadataWithBucket
from ..auth.depends import AuthenticatedAdmin

bucket = APIRouter()


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
    await write_meta(meta_location, meta)

    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # end with
# end def


@bucket.get("/file/{bucket}/{file_id}")
async def get_file(
    file_id: UUID,
    bucket: Bucket,
    dl: bool = False,
):
    locations = await check_file_paths(bucket, file_id)
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
    locations = await check_file_paths(bucket, file_id)
    if file_id not in metadata_store:
        raise HTTPException(status_code=404, detail="Metadata not found")
    # end if
    return metadata_store[file_id]
# end def