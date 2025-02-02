from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse
from uuid import UUID

import uuid6
import shutil

from .paths import UPLOAD_DIR, calculate_file_paths, get_file_metadata
from .depends import UploadedFile, Now
from .io import write_meta
from .models import Bucket, FileId
from .models import FileMetadataWithBucket
from ..auth.depends import AuthenticatedAdmin
from ..auth.models import AccessLevel

bucket = APIRouter()


# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


@bucket.post("/upload/{bucket}")
async def upload_file(
    bucket: Bucket,
    file: UploadedFile,
    user: AuthenticatedAdmin,
    now: Now,
    access_level: AccessLevel,
):
    if not user:
        raise HTTPException(status_code=403, detail="Not authorized to upload files")
    # end if

    file_id = uuid6.uuid7()
    locations = calculate_file_paths(bucket, file_id)
    locations.bucket.mkdir(exist_ok=True)

    meta = FileMetadataWithBucket(
        bucket=bucket,
        file_id=file_id,
        access_level=access_level,
        original_name=file.filename,
        size=file.size,
        uploaded_by=user.username,
        uploaded_at=now,
        content_type=file.content_type,
        headers=file.headers,
    )
    await write_meta(locations.meta, meta)

    with open(locations.file, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # end with
# end def


@bucket.get("/file/{bucket}/{file_id}")
async def get_file(
    file_id: FileId,
    bucket: Bucket,
    dl: bool = False,
):
    info = await get_file_metadata(bucket, file_id)
    if dl:
        return FileResponse(info.locations.file, media_type='application/octet-stream', filename=info.meta.original_name)
    else:
        return FileResponse(info.locations.file)
    # end if
# end def


@bucket.get("/metadata/{bucket}/{file_id}", response_model=FileMetadataWithBucket)
async def get_metadata(
    file_id: FileId,
    bucket: Bucket,
):
    info = await get_file_metadata(bucket, file_id)
    return info.meta.as_with_bucket(bucket=bucket)
# end def