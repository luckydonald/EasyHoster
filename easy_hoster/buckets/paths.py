from uuid import UUID

from fastapi import HTTPException

from .models import Bucket, GetFilePaths, GetFileMetadata
from .io import read_meta

from pathlib import Path


# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")


def calculate_file_paths(
    bucket: Bucket,
    file_id: UUID,
) -> GetFilePaths:
    folder = UPLOAD_DIR / bucket
    file_location = folder / f"{file_id}.blob"
    meta_location = folder / f"{file_id}.meta"
    return GetFilePaths(file_location, meta_location, folder)
# end def


async def check_file_paths(
    bucket: Bucket,
    file_id: UUID,
) -> GetFilePaths:
    locations = calculate_file_paths(bucket, file_id)
    if not locations.file.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    # end if
    if not locations.meta.exists():
        raise HTTPException(status_code=404, detail="Metadata not found on disk")
    # end def
    return locations
# end def


async def get_file_metadata(
    bucket: Bucket,
    file_id: UUID,
) -> GetFileMetadata:
    locations = await check_file_paths(bucket, file_id)
    meta = read_meta(locations.meta)
    return GetFileMetadata(locations.file, meta)
# end def
