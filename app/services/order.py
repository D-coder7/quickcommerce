from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.repositories.catalog import ProductRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.order import OrderRepository
from app.services.cart import CartService
from app.schemas.order import OrderCreate
from app.models.order import OrderStatus
from app.core.logging import get_logger

log = get_logger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.db = db
        self.product_repo = ProductRepository(db)
        self.inv_repo = InventoryRepository(db)
        self.order_repo = OrderRepository(db)
        self.cart_service = CartService(db, redis)

    async def checkout(self, user_id: int, data: OrderCreate):
        cart_items = await self.cart_service.get_raw_items(user_id)
        if not cart_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

        product_ids = list(cart_items.keys())
        products = await self.product_repo.get_by_ids(product_ids)
        product_map = {p.id: p for p in products}

        order_items = []
        total = 0.0
        reserved_products = []

        for product_id, quantity in cart_items.items():
            product = product_map.get(product_id)
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {product_id} is no longer available",
                )

            reserved = await self.inv_repo.reserve(product_id, quantity)
            if not reserved:
                for prev_id, prev_qty in reserved_products:
                    await self.inv_repo.release_reservation(prev_id, prev_qty)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}",
                )
            reserved_products.append((product_id, quantity))

            unit_price = float(product.price)
            total += unit_price * quantity
            order_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
            })

        order = await self.order_repo.create(
            user_id=user_id,
            total_amount=round(total, 2),
            delivery_address=data.delivery_address,
            notes=data.notes,
            items=order_items,
        )

        for product_id, quantity in cart_items.items():
            await self.inv_repo.confirm_sale(product_id, quantity)

        await self.cart_service.clear_cart(user_id)

        log.info("order.created", order_id=order.id, user_id=user_id, total=round(total, 2))

        # reload with items populated (lazy="noload" means the in-memory object has empty list)
        return await self.order_repo.get_by_id(order.id)

    async def get_user_orders(self, user_id: int):
        return await self.order_repo.get_user_orders(user_id)

    async def get_order(self, order_id: int, user_id: int):
        order = await self.order_repo.get_by_id(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    async def update_status(self, order_id: int, new_status: OrderStatus):
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return await self.order_repo.update_status(order, new_status)
