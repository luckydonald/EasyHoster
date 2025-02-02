from datetime import timedelta, datetime, timezone

import jwt

from .env import SECRET, ALGORITHM
from .models import TokenData


def create_access_token(data: TokenData, expires_delta: timedelta | None = None):
    """
    Note, `data.expires_at` is set in this function.

    :param data:
    :param expires_delta:
    :return:
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    # end if
    data.expires_at = expire
    to_encode = data.model_dump(mode="json")
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt
# end def


def parse_token_data(token: str):
    return TokenData(**jwt.decode(token, SECRET, algorithms=[ALGORITHM]))
# end def
