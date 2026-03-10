from pydantic import BaseModel, Field


class CreateUserIn(BaseModel):
    worker_id: int
    is_admin: bool = False


class UpdateUserAdminIn(BaseModel):
    is_admin: bool


class AdminResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=8)
