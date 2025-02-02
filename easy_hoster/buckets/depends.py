__all__ = (
    "UploadedFile",
    "Now",
)

from datetime import datetime
from typing import Annotated

from fastapi import UploadFile, File, Depends

from .depends_funcs import now


UploadedFile = Annotated[UploadFile, File(description="A file read as UploadFile")]

Now = Annotated[datetime, Depends(now)]
