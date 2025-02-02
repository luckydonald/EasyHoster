from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)
# end def


def verify_password(*, password, hash):
    return pwd_context.verify(password, hash)
# end def
