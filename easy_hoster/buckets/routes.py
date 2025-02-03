
from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse

import uuid6

import shutil
import logging

from starlette import status

from .paths import UPLOAD_DIR, calculate_file_paths, get_file_metadata, calculate_bucket_folder
from .depends import UploadedFile, Now, AuthenticatedMatchesMeta, FormField, AuthenticatedUploader
from .io import write_meta, read_meta
from .models import Bucket, FileId, AllowedRoles, UploadFileResult, FileMetadataWithBucket
from ..auth.core import current_user_has_role
from ..auth.depends import AuthenticatedAdmin, AuthenticatedUserOrNone


buckets = APIRouter()
logger = logging.getLogger(__name__)


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


@buckets.get("/{bucket}", status_code=201)
async def list_bucket(
    user: AuthenticatedUserOrNone,
    bucket: Bucket,
) -> dict[FileId, FileMetadataWithBucket]:
    blob_files = {}
    for meta_file in calculate_bucket_folder(bucket).glob("*.meta"):
        blob_file = meta_file.with_suffix(".blob")
        file_id = FileId(meta_file.with_suffix('').name)
        if not blob_file.exists():
            logger.warning(f'Bucket {bucket} is missing data .blob for {file_id}.')
            continue
        # end def
        meta = await read_meta(meta_file)
        for role in meta.allowed_roles:
            try:
                user = current_user_has_role(role)
            except HTTPException:
                continue
            # end try
            if user is None:
                continue
            # end if
            blob_files[file_id] = meta.as_with_bucket(bucket=bucket)
            break
        else:  # never did 'break' -> nothing found
            continue
        # end for
    # end def
    return blob_files
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
