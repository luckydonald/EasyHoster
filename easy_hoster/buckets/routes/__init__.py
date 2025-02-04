from fastapi import APIRouter

from .bucket import buckets
from .file import files
from .webdav import webdav
from ..constants import TAG

api = APIRouter()
api.include_router(buckets, prefix="", tags=[f"{TAG}.bucket"])
api.include_router(files, prefix="", tags=[f"{TAG}.file"])
api.include_router(webdav, prefix="", tags=[f"{TAG}.webdav"])
