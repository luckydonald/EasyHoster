# noinspection PyUnresolvedReferences
from easy_hoster.main import app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# end if
