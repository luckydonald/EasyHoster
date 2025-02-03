from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse

import uuid6
import shutil

from starlette import status

from .paths import UPLOAD_DIR, calculate_file_paths, get_file_metadata
from .depends import UploadedFile, Now, AuthenticatedMatchesMeta, FormField, AuthenticatedUploader
from .io import write_meta
from .models import Bucket, FileId, AllowedRoles, UploadFileResult, FileMetadataWithBucket
from ..auth.depends import AuthenticatedAdmin

buckets = APIRouter()


# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


@buckets.put("/{bucket}", response_model=UploadFileResult, status_code=201)
async def upload_file(
    user: AuthenticatedAdmin,
    bucket: Bucket,
    file: UploadedFile,
    now: Now,
    access_level: FormField(AllowedRoles, 'access_level'),
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
        allowed_roles=access_level,
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
    return UploadFileResult(
        file_id=file_id,
    )
# end def


@buckets.get("/{bucket}/{file_id}")
async def get_file(
    _: AuthenticatedMatchesMeta,
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


@buckets.get("/{bucket}/{file_id}/metadata", response_model=FileMetadataWithBucket)
async def get_metadata(
    _: AuthenticatedMatchesMeta,
    file_id: FileId,
    bucket: Bucket,
):
    info = await get_file_metadata(bucket, file_id)
    return info.meta.as_with_bucket(bucket=bucket)
# end def


@buckets.delete("/{bucket}/{file_id}")
async def delete_file(
    _: AuthenticatedUploader,
    file_id: FileId,
    bucket: Bucket,
) -> None:
    locations = calculate_file_paths(bucket, file_id)
    something_existed: bool = False
    if locations.file.exists():
        locations.file.unlink()
        something_existed = True
    # end if
    if locations.meta.exists():
        locations.meta.unlink()
        something_existed = True
    # end if
    if not something_existed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    # end if
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Deleted")
# end if
