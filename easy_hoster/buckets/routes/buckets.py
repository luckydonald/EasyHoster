import inspect

from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse

import uuid6

import shutil
import logging

from starlette import status
from starlette.requests import Request

from ..depends_funcs import current_user_has_effective_role
from ..paths import UPLOAD_DIR, calculate_file_paths, get_file_metadata, calculate_bucket_folder
from ..depends import UploadedFile, Now, AuthenticatedMatchesMeta, FormField, AuthenticatedUploader
from ..io import write_meta, read_meta
from ..models import Bucket, FileId, AllowedRoles, FileMetadataWithBucket, EffectiveRole, \
    FileMetadataForApi
from easy_hoster.auth.depends import AuthenticatedAdmin, AuthenticatedUserOrNone


buckets = APIRouter()
logger = logging.getLogger(__name__)


# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)


@buckets.put("/{bucket}", status_code=201)
async def upload_file(
    user: AuthenticatedAdmin,
    request: Request,
    *,
    bucket: Bucket,
    file: UploadedFile,
    now: Now,
    access_level: FormField(AllowedRoles, 'access_level'),
) -> FileMetadataForApi:
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
    return meta.as_api(request=request)
# end def


@buckets.get("/{bucket}", status_code=201)
async def list_bucket(
    current_user: AuthenticatedUserOrNone,
    request: Request,
    bucket: Bucket,
) -> list[FileMetadataForApi]:
    blob_files = []
    for meta_file in calculate_bucket_folder(bucket).glob("*.meta"):
        blob_file = meta_file.with_suffix(".blob")
        file_id = FileId(meta_file.with_suffix('').name)
        if not blob_file.exists():
            logger.warning(f'Bucket {bucket} is missing data .blob for {file_id}.')
            continue
        # end def
        meta = await read_meta(meta_file)
        possible_params = dict(current_user=current_user, bucket=bucket, file_id=file_id)
        for role_value, is_enabled in meta.allowed_roles:
            if not is_enabled:
                continue
            # end if
            role = EffectiveRole(role_value)
            try:
                checker = current_user_has_effective_role(role)
                signature = inspect.signature(checker)
                kwargs = {
                    key : value
                    for key, value in possible_params.items()
                    if key in signature.parameters.keys()
                }
                user = await checker(**kwargs)
            except HTTPException as e:
                continue
            # end try
            if user is None and role is not EffectiveRole.UNAUTHENTICATED:
                continue
            # end if
            blob_files.append(meta.as_api(request=request, bucket=bucket))
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
        return FileResponse(path=info.locations.file, media_type='application/octet-stream', filename=info.meta.original_name)
    else:
        return FileResponse(path=info.locations.file, media_type=info.meta.content_type)
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
