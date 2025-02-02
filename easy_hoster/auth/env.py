import os

SECRET = os.environ.get('JWT_SECRET', '')
if not SECRET:
    raise EnvironmentError('No JWT_SECRET environment variable set.')
# end if

ALGORITHM = os.environ.get('JWT_ALGORITHM', "HS256")
if not ALGORITHM:
    raise EnvironmentError('No JWT_ALGORITHM environment variable set.')
# end if

TOKEN_EXPIRE_MINUTES = os.environ.get('JWT_TOKEN_EXPIRE_MINUTES', '30')
if not TOKEN_EXPIRE_MINUTES:
    raise EnvironmentError('No JWT_TOKEN_EXPIRE_MINUTES environment variable set.')
# end if
TOKEN_EXPIRE_MINUTES = int(TOKEN_EXPIRE_MINUTES)
