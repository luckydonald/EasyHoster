from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .auth.depends import Token
from .auth.routes import auth

app = FastAPI()

app.include_router(auth)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/items/")
async def read_items(token: Token):
    return {"token": token}