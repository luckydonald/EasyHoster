from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from pydantic import HttpUrl
from starlette.convertors import CONVERTOR_TYPES
from uuid import UUID



def add_query(url: str | HttpUrl, **kwargs: str | bool) -> str:
    parsed = urlparse(str(url))
    query = parse_qs(parsed.query)
    for key, value in kwargs.items():
        if key not in query:
            query[key] = []
        # end if
        if isinstance(value, int):
            converter = CONVERTOR_TYPES['int']
        elif isinstance(value, float):
            converter = CONVERTOR_TYPES['float']
        elif isinstance(value, str):
            converter = CONVERTOR_TYPES['str']
        elif isinstance(value, UUID):
            converter = CONVERTOR_TYPES['uuid']
        else:
            converter = CONVERTOR_TYPES['str']
        # end if
        str_value = converter.to_string(value)

        query[key].append(str_value)
    # end for
    new_query = urlencode(query, doseq=True)
    new_parsed: tuple[str] = parsed._replace(query=new_query)
    new_url = urlunparse(new_parsed)
    return new_url
# end def
