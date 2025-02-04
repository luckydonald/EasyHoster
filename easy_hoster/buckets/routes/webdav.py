from pathlib import Path

from fastapi import Request, Response, APIRouter
import os

from .bucket import list_bucket
from .file import get_file
from ..depends import AuthenticatedMatchesMeta
from ..models import Bucket, FileId
from ..paths import UPLOAD_DIR
from ...auth.depends import AuthenticatedUserOrNone
from ...utils import hint

webdav = APIRouter()


@webdav.options("/webdav/{path:path}")
async def webdav_options(request: Request, path: str):
    """
    Handle OPTIONS requests for WebDAV.
    """
    response = Response(status_code=200)
    response.headers["Allow"] = "GET, PUT, DELETE, OPTIONS"
    response.headers["DAV"] = "1, 2"
    return response
# end def


@webdav.get("/webdav/")
async def webdav_get_root():
    names = [hint(Path, p).name for p in UPLOAD_DIR.iterdir() if p.is_file()]
    return Response(content="\n".join(names), media_type="text/plain")
# end def



@webdav.get("/webdav/{bucket}")
async def webdav_get_bucket(
    current_user: AuthenticatedUserOrNone,
    request: Request,
    bucket: Bucket,
):
    files = await list_bucket(
        current_user=current_user,
        request=request,
        bucket=bucket,
    )
    names = [file.file_id for file in files]
    return Response(content="\n".join(names), media_type="text/plain")
# end def


@webdav.get("/webdav/{bucket}/{file_id}")
async def webdav_get_bucket(
    _: AuthenticatedMatchesMeta,
    bucket: Bucket,
    file_id: FileId,
):
    return await get_file(
        _=_,
        bucket=bucket,
        file_id=file_id,
        dl=False,
    )
# end def


@webdav.get("/webdav/{path:path}")
async def webdav_get(request: Request, path: str):
    """
    Handle stray requests, which are allowed per WebDAV specification.
    """
    return Response(status_code=404)
# end def


@webdav.put("/webdav/{path:path}")
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


@webdav.delete("/webdav/{path:path}")
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
