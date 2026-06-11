from pydantic import BaseModel
from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    delivery_address: str
    notes: str | None = None


class OrderItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    product_id: int
    quantity: int
    unit_price: float
    subtotal: float = 0.0

    def model_post_init(self, __context) -> None:
        object.__setattr__(self, "subtotal", round(self.quantity * self.unit_price, 2))


class OrderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    status: OrderStatus
    total_amount: float
    delivery_address: str
    notes: str | None
    items: list[OrderItemResponse] = []


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
