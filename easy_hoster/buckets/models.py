
BUCKET_PATTERN = "^[a-zA-Z0-9_-]+$"

Bucket = Annotated[str, Doc("Where it's stored in"), Field(pattern=BUCKET_PATTERN)]
