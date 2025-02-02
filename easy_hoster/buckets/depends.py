__all__ = (
    "UploadedFile",
)

from datetime import datetime
from typing import Annotated

from fastapi import UploadFile, File, Depends


UploadedFile = Annotated[UploadFile, File(description="A file read as UploadFile")]

Bucket = Annotated[str, Doc("Where it's stored in"), Field(pattern=BUCKET_PATTERN)]

