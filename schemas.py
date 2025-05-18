from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., ge=0, description="Price must be non-negative")
    quantity: Optional[int] = Field(None, gt=0, description="Quantity must be greater than zero")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, gt=0)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v

class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True

