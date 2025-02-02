from pathlib import Path
from typing import Annotated, Optional, Union

from starlette.datastructures import Headers
from typing_extensions import Doc

from fastapi import UploadFile, File, HTTPException, Depends, Header, APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import os
import uuid
import shutil
from passlib.context import CryptContext
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

from pydantic.v1 import UUID5

from ..auth.models import FullUser


BUCKET_PATTERN = "^[a-zA-Z0-9_-]+$"

bucket = APIRouter()


# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")

# Dependency for authorization
def get_current_user(
    authorize: Annotated[Union[str, None], Header()] = None
) -> User:
    try:
        AuthJWT().jwt_required()
        username = AuthJWT().get_jwt_subject()
        if username not in users:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return users[username]
    except AuthJWTException:
        raise HTTPException(status_code=401, detail="Invalid token")

def authorize_user(user: User = Depends(get_current_user)):
    if user.username != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to perform this action")
    return True

# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

# Metadata model
class FileMetadata(BaseModel):
    original_name: str
    uploaded_by: str
    uploaded_at: str
    version: int
    file_id: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
@AuthJWT.load_config
def get_config():
    return JWTSettings()

class JWTSettings(BaseModel):
    authjwt_secret_key: str = "your-secret-key"

class User(BaseModel):
    username: str
    hashed_password: str

# In-memory storage for users (could be replaced with a database)
users = {
    "admin": User(username="admin", hashed_password=pwd_context.hash("admin_password"))
}


# Dependency for authorization (dummy implementation)
def authorize_user():
    # Implement your authorization logic here
    return True
# end def


class Meta(BaseModel):
    bucket: Annotated[str, Doc("Where it's stored in")] = Field(pattern=BUCKET_PATTERN)
    file_id: Annotated[uuid.UUID, Doc("new UUID file name.")]

    filename: Annotated[Optional[str], Doc("The original file name.")]
    size: Annotated[Optional[int], Doc("The size of the file in bytes.")]
    content_type: Annotated[
        Optional[str], Doc("The content type of the request, from the headers.")
    ]

    headers: Annotated[Headers, Doc("The headers of the request.")]
# end class


@bucket.post("/upload/{bucket}")
async def upload_file(
    bucket: str = Field(pattern=BUCKET_PATTERN),
    file: UploadFile = File(...),
    authorized: bool = Depends(authorize_user),
    user: FullUser = Depends(get_current_user),
):
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to upload files")

    file_id = uuid.uuid4()
    folder = UPLOAD_DIR / bucket
    folder.mkdir(exist_ok=True)
    file_location = folder / f"{file_id!s}.blob"
    meta_location = folder / f"{file_id!s}.meta"

    meta = Meta(
        bucket=bucket,
        file_id=file_id,
        filename=file.filename,
        size=file.size,
        headers=file.headers,
        content_type=file.content_type,
    )
    with open(meta_location, "w") as f:
        data = object()
        data.foo = file.filename
        f.write(meta.model_dump_json())
    # end with

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # end with
# end def


@bucket.get("/files/{bucket}/{file_id}")
async def get_file(
    file_id: uuid.UUID,
    bucket: str = Field(pattern=BUCKET_PATTERN),
    dl: bool = False,
):
    if file_id not in metadata_store:
        raise HTTPException(status_code=404, detail="File not found")

    file_id = str(uuid.uuid4())
    folder = UPLOAD_DIR / bucket
    folder.mkdir(exist_ok=True)
    file_location = folder / f"{file_id}.blob"
    meta_location = folder / f"{file_id}.meta"

    if not os.path.exists(file_location) or not os.path.exists(meta_location):
        raise HTTPException(status_code=404, detail="File not found on disk")
    # end if
    if dl:
        return FileResponse(file_location, media_type='application/octet-stream', filename=metadata_store[file_id].original_name)
    else:
        return FileResponse(file_location)
    # end if
# end def

@bucket.get("/metadata/{file_id}")
async def get_metadata(file_id: str):
    if file_id not in metadata_store:
        raise HTTPException(status_code=404, detail="Metadata not found")
    # end if
    return metadata_store[file_id]
# end def