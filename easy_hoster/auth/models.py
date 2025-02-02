from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "normal"

class User(BaseModel):
    username: str
    role: str
