from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ..crypt import verify_password
from ..models import Token, TokenData
from ..io import user_store
from ..env import TOKEN_EXPIRE_MINUTES
from ..token import create_access_token

oauth_password = APIRouter()


OAuthPasswordForm = Annotated[OAuth2PasswordRequestForm, Depends()]

@oauth_password.post("/token")
async def login(form_data: OAuthPasswordForm) -> Token:
    # if form_data.scopes != ["mango"]:
    #     raise HTTPException(status_code=400, detail='Incorrect scope: Must be "mango".')
    # '# end if
    if form_data.username not in user_store:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # end if
    stored_user = user_store.get(form_data.username)
    user = stored_user.to_full(username=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # end if
    if not verify_password(password=form_data.password, hash=user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # end if

    access_token_expires = timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=TokenData(
            username=user.username,
        ), expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
# end def
