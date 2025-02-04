from fastapi import HTTPException, APIRouter
from starlette import status
from starlette.responses import FileResponse

from ..depends import AuthenticatedMatchesMeta, AuthenticatedUploader
from ..models import FileId, Bucket, FileMetadataWithBucket
from ..paths import get_file_metadata, calculate_file_paths


files = APIRouter()

@files.get("/{bucket}/{file_id}")
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


@files.get("/{bucket}/{file_id}/metadata", response_model=FileMetadataWithBucket)
async def get_metadata(
    _: AuthenticatedMatchesMeta,
    file_id: FileId,
    bucket: Bucket,
):
    info = await get_file_metadata(bucket, file_id)
    return info.meta.as_with_bucket(bucket=bucket)
# end def


@files.delete("/{bucket}/{file_id}")
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
# end def
