from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .auth.routes import auth
from .auth.constants import ROUTE_PREFIX as AUTH_ROUTE_PREFIX, TAG as AUTH_TAG
from .buckets.routes import api as buckets
from .buckets.constants import ROUTE_PREFIX as BUCKET_ROUTE_PREFIX, TAG as BUCKET_TAG

app = FastAPI()

app.include_router(auth, prefix=AUTH_ROUTE_PREFIX, tags=[AUTH_TAG])
app.include_router(buckets, prefix=BUCKET_ROUTE_PREFIX, tags=[BUCKET_TAG])


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
