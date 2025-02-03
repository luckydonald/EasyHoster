from fastapi import HTTPException
from starlette import status

TAG = "auth"
ROUTE_PREFIX = '/auth'
OAUTH_ROUTE_PREFIX = ''


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
