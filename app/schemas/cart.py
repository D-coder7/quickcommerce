from pydantic import BaseModel, field_validator


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class CartItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total: float
    item_count: int
