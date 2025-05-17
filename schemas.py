from pydantic import BaseModel
from typing import Optional

# Common base fields for items
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    quantity: Optional[int] = None

# Schema for creating a new item (all fields required)
class ItemCreate(ItemBase):
    pass

# Schema for reading/returning an item (includes ID)
class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
