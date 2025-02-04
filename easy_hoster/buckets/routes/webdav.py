from fastapi import Request, Response, APIRouter
from starlette.responses import FileResponse
import os


app = APIRouter()

# Set the root directory for WebDAV access
WEBDAV_ROOT_DIR = "/path/to/your/webdav/root"


@app.options("/webdav/{path:path}")
async def webdav_options(request: Request, path: str):
    """
    Handle OPTIONS requests for WebDAV.
    """
    response = Response(status_code=200)
    response.headers["Allow"] = "GET, PUT, DELETE, OPTIONS"
    response.headers["DAV"] = "1, 2"
    return response
# end def



@app.get("/webdav/{path:path}")
async def webdav_get(request: Request, path: str):
    """
    Handle GET requests for WebDAV.
    """
    full_path = os.path.join(WEBDAV_ROOT_DIR, path)
    if os.path.isfile(full_path):
        return FileResponse(full_path)
    elif os.path.isdir(full_path):
        # Return a list of files and directories in the directory
        contents = os.listdir(full_path)
        return Response(content="\n".join(contents), media_type="text/plain")
    else:
        return Response(status_code=404)
    # end if
# end def


@app.put("/webdav/{path:path}")
async def webdav_put(request: Request, path: str):
    """
    Handle PUT requests for WebDAV.
    """
    full_path = os.path.join(WEBDAV_ROOT_DIR, path)
    directory = os.path.dirname(full_path)
    os.makedirs(directory, exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(await request.body())
    # end with
    return Response(status_code=201)
# end def


@app.delete("/webdav/{path:path}")
async def webdav_delete(request: Request, path: str):
    """
    Handle DELETE requests for WebDAV.
    """
    full_path = os.path.join(WEBDAV_ROOT_DIR, path)
    if os.path.isfile(full_path):
        os.remove(full_path)
    elif os.path.isdir(full_path):
        os.rmdir(full_path)
    return Response(status_code=204)
# end def
