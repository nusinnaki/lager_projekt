from typing import Optional

from pydantic import BaseModel


class ActionIn(BaseModel):
    product_id: int
    quantity: int


class ProductCreateIn(BaseModel):
    kind: str
    nc_nummer: Optional[str] = None
    product_name: str
