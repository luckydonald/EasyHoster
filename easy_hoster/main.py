from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from easy_hoster.auth.depends import Token

app = FastAPI()

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