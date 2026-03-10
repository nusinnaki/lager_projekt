from pydantic import BaseModel


class CreateUserIn(BaseModel):
    worker_id: int
    is_admin: bool = False


class UpdateUserAdminIn(BaseModel):
    is_admin: bool
