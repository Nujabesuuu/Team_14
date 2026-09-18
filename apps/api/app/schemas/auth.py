import uuid
from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import OrmModel


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=40)
    birth_date: date


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AccountOut(OrmModel):
    id: uuid.UUID
    email: str
    display_name: str
    age: int
    is_premium: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AccountOut
