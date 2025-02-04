from fastapi import APIRouter

from .buckets import buckets
from ..constants import TAG

api = APIRouter()
api.include_router(buckets, prefix="", tags=[f"{TAG}.bucket"])