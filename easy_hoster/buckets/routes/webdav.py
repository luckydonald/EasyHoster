from pathlib import Path
from mimetypes import guess_extension
from time import ctime
from typing import Annotated

from fastapi import Request, Response, APIRouter, HTTPException, Depends

import os

from starlette import status

from .bucket import list_bucket
from .file import get_file
from .templates import templates
from ..depends_funcs import current_user_has_effective_role_matching_meta
from ..models import Bucket, FileId
from ..paths import UPLOAD_DIR, get_file_metadata, calculate_file_paths
from ..utils.permissions import file_permissions
from ...auth.basic_auth.depends import AuthenticatedUserOrNone
from ...auth.models import FullUser

webdav = APIRouter()

async def current_user_has_effective_role_matching_meta_in_basic_auth(
    current_user: AuthenticatedUserOrNone,
    bucket: Bucket,
    file_id: FileId,
) -> None:
    return await current_user_has_effective_role_matching_meta(current_user, bucket, file_id)
# end def

AuthenticatedMatchesMeta = Annotated[FullUser, Depends(current_user_has_effective_role_matching_meta_in_basic_auth)]

@webdav.options("/webdav")
@webdav.options("/webdav/")
async def webdav_options():
    response = Response(status_code=status.HTTP_200_OK)
    response.headers["Allow"] = "GET, OPTIONS, PROPFIND"  # TODO: re-enable PUT, DELETE
    response.headers["DAV"] = "1"  # TODO: maybe implement 2, so we can write `"1, 2"`.
    return response
# end def


@webdav.options("/webdav/{bucket}")
@webdav.options("/webdav/{bucket}/")
async def webdav_options(bucket: Bucket):
    response = Response(status_code=status.HTTP_200_OK)
    response.headers["Allow"] = "GET, OPTIONS, PROPFIND"  # TODO: re-enable PUT, DELETE
    return response
# end def


@webdav.options("/webdav/{bucket}/{file_id}")
@webdav.options("/webdav/{bucket}/{file_id}.{ext}")
async def webdav_options(bucket: Bucket, file_id: FileId, ext: str | None = None):
    response = Response(status_code=status.HTTP_200_OK)
    response.headers["Allow"] = "GET, OPTIONS"  # TODO: re-enable PUT, DELETE
    return response
# end def


def get_files_root() -> list[Path]:
    return [p for p in UPLOAD_DIR.iterdir() if p.is_dir()]
# end def


@webdav.get("/webdav/")
async def webdav_get_root():
    names = [file.name for file in get_files_root()]
    return Response(content="\n".join(names), media_type="text/plain")
# end def


@webdav.api_route("/webdav/", methods=["PROPFIND"])
async def webdav_propfind_root(request: Request):
    items = [
        {
            "path": file.name,
            "is_file": False,  # all buckets are folders
        }
        for file in get_files_root()
    ]
    return templates.TemplateResponse(
        request=request, name="webdav_propfind.jinja2", context=dict(items=items)
    )
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


def get_webdav_suffix(content_type: str, original_name: str) -> str:
    """ The suffix, starting with a dot. """
    ext = guess_extension(content_type)
    if ext is None:
        suffixes = Path(original_name).suffixes
        if not suffixes:
            return '.unknown'
        # end if
        if len(suffixes) == 1:
            return suffixes[0]
        # end if
        if suffixes[0] == ".tar":
            return "".join(suffixes)
        # end def
        return suffixes[-1]
    # end if
    return ext
# end def



@webdav.api_route("/webdav/{bucket}/", methods=["PROPFIND"])
async def webdav_propfind_bucket(
    current_user: AuthenticatedUserOrNone,
    request: Request,
    bucket: Bucket,
):
    metas = await list_bucket(
        current_user=current_user,
        request=request,
        bucket=bucket,
    )
    items = []
    for meta in metas:
        paths = calculate_file_paths(bucket=bucket, file_id=meta.file_id)
        item = {
            "path": f"{meta.file_id}{get_webdav_suffix(meta.content_type, meta.original_name)}",
            "is_file": True,  # no folders in the buckets
            "mime": meta.content_type,
            'size': meta.size, # paths.file.stat().st_size if paths.file.is_file() else None,  # Size in bytes
            'last_modified': ctime(paths.file.stat().st_mtime),  # Last modified time
            'creation_date': meta.uploaded_at.isoformat(), # ctime(paths.file.stat().st_ctime),  # Creation time
            'etag': f'"{paths.file.stat().st_ino}-{paths.file.stat().st_mtime}"',  # Simple ETag based on inode and mtime
        }
        if current_user and current_user.is_admin:
            item['owner'] = meta.uploaded_by  # os.stat(paths.file).st_uid  # Owner UID
            item['group'] = 'admin'
            item['permissions'] = file_permissions(meta.allowed_roles)  # oct(paths.file.stat().st_mode)[-3:]  # Permissions in octal
        # end if
        items.append(item)
    # end for
    return templates.TemplateResponse(
        request=request, name="webdav_propfind.jinja2", context=dict(items=items)
    )
# end def


@webdav.get("/webdav/{bucket}/{file_id}.{ext}")
async def webdav_get_bucket_with_ext(
    _: AuthenticatedMatchesMeta,
    bucket: Bucket,
    file_id: FileId,
    ext: str,
):
    info = await get_file_metadata(bucket=bucket, file_id=file_id)
    expected_ext = get_webdav_suffix(info.meta.content_type, info.meta.original_name)
    if f".{ext}" != expected_ext:
        raise HTTPException(status_code=404, detail="File not found (extension mismatch).")
    # end if
    return await get_file(
        _=_,
        bucket=bucket,
        file_id=file_id,
        dl=False,
    )
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


@webdav.api_route("/webdav/{path:path}", methods=["PROPFIND"])
async def webdav_propfind_fallback(request: Request, path: str):
    """
    Handle stray requests, which are allowed per WebDAV specification. Return 404.
    """
    return Response(status_code=404)
# end def


@webdav.get("/webdav/{path:path}")
async def webdav_get_fallback(request: Request, path: str):
    """
    Handle stray requests, which are allowed per WebDAV specification. Return 404.
    """
    return Response(status_code=404)
# end def


@webdav.put("/webdav/{path:path}")
async def webdav_put(request: Request, path: str):
    """
    Handle PUT requests for WebDAV.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
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
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
    full_path = os.path.join(WEBDAV_ROOT_DIR, path)
    if os.path.isfile(full_path):
        os.remove(full_path)
    elif os.path.isdir(full_path):
        os.rmdir(full_path)
    return Response(status_code=204)
# end def
