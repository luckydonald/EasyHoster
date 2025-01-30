from pathlib import Path
from typing import Annotated, Optional

from starlette.datastructures import Headers
from typing_extensions import Doc

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import uuid
import shutil

from pydantic.v1 import UUID5

BUCKET_PATTERN = "^[a-zA-Z0-9_-]+$"

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")

# Ensure the upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

# Metadata model
class FileMetadata(BaseModel):
    original_name: str
    file_id: str

# In-memory storage for metadata (could be replaced with a database)
metadata_store = {}


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


@app.post("/upload/{bucket}")
async def upload_file(
    bucket: str = Field(pattern=BUCKET_PATTERN),
    file: UploadFile = File(...),
    authorized: bool = Depends(authorize_user),
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


@app.get("/files/{bucket}/{file_id}")
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

    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="File not found on disk")

    if dl:
        return FileResponse(file_location, media_type='application/octet-stream', filename=metadata_store[file_id].original_name)
    else:
        return FileResponse(file_location)

@app.get("/metadata/{file_id}")
async def get_metadata(file_id: str):
    if file_id not in metadata_store:
        raise HTTPException(status_code=404, detail="Metadata not found")

    return metadata_store[file_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
