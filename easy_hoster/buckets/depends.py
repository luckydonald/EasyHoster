__all__ = (
    "UploadedFile",
    "Bucket",
)

from typing import Annotated

from pydantic import Field
from typing_extensions import Doc

from fastapi import UploadFile, File

from .models import BUCKET_PATTERN


UploadedFile = Annotated[UploadFile, File(description="A file read as UploadFile")]

Bucket = Annotated[str, Doc("Where it's stored in"), Field(pattern=BUCKET_PATTERN)]

