from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import shutil

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
UPLOAD_DIR = "uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), authorized: bool = Depends(authorize_user)):
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to upload files")

    file_id = str(uuid.uuid4())
    file_location = os.path.join(UPLOAD_DIR, file_id)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store metadata
    metadata_store[file_id] = FileMetadata(original_name=file.filename, file_id=file_id)

    return {"file_id": file_id, "original_name": file.filename}

@app.get("/files/{file_id}")
async def get_file(file_id: str, dl: bool = False):
    if file_id not in metadata_store:
        raise HTTPException(status_code=404, detail="File not found")

    file_location = os.path.join(UPLOAD_DIR, file_id)

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
