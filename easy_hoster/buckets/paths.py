from uuid import UUID

from fastapi import HTTPException

from .models import Bucket, GetFilePaths, GetFileMetadata

from pathlib import Path


# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")


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