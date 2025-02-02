from pathlib import Path

from .models import FileMetadata, FileMetadataWithBucket


async def write_meta(
    path: Path,
    meta: FileMetadata | FileMetadataWithBucket,
):
    with open(path, "w") as f:
        f.write(
            meta.model_dump_json(
                indent=2,
            )
        )
    # end with
# end def


async def read_meta(
    path: Path,
) -> FileMetadata:
    with open(path, "r") as f:
        data = f.read()
    # end with
    return FileMetadata(**data)
# end def
