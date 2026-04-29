from pydantic import BaseModel, Field


class ActionIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class ProductLocationIn(BaseModel):
    location_id: int