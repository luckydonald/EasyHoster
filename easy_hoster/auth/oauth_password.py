from fastapi import APIRouter, HTTPException

from .core import verify_password
from .depends import OAuthPasswordForm
from .io import user_store

oauth_password = APIRouter


@oauth_password.post("/token")
async def login(form_data: OAuthPasswordForm):
    stored_user = user_store.get(form_data.username)
    user = stored_user.to_full(username=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(password=form_data.password, hash=user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}
