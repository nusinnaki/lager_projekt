from pydantic import BaseModel, Field


class SetPasswordIn(BaseModel):
    username: str
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class LoginOut(BaseModel):
    access_token: str
    token_type: str
    user: dict
