from pydantic import BaseModel, field_validator


class InventoryCreate(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


class InventoryUpdate(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


class InventoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    product_id: int
    quantity: int
    reserved: int
    available: int
