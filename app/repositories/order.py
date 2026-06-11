from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.order import Order, OrderItem, OrderStatus


class OrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        user_id: int,
        total_amount: float,
        delivery_address: str,
        notes: str | None,
        items: list[dict],
    ) -> Order:
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            delivery_address=delivery_address,
            notes=notes,
        )
        self.db.add(order)
        await self.db.flush()

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            self.db.add(order_item)

        await self.db.flush()
        return order

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(joinedload(Order.items))
            .where(Order.id == order_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_user_orders(self, user_id: int) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .options(joinedload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.unique().scalars().all())

    async def update_status(self, order: Order, status: OrderStatus) -> Order:
        order.status = status
        await self.db.flush()
        return order
