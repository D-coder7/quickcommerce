import json
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.repositories.catalog import ProductRepository
from app.repositories.inventory import InventoryRepository
from app.schemas.cart import CartItemAdd, CartItemResponse, CartResponse

CART_TTL = 3600  # 1 hour


def _cart_key(user_id: int) -> str:
    return f"cart:{user_id}"


class CartService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.product_repo = ProductRepository(db)
        self.inv_repo = InventoryRepository(db)
        self.redis = redis

    async def get_cart(self, user_id: int) -> CartResponse:
        raw = await self.redis.hgetall(_cart_key(user_id))
        if not raw:
            return CartResponse(items=[], total=0.0, item_count=0)

        product_ids = [int(k) for k in raw.keys()]
        products = await self.product_repo.get_by_ids(product_ids)
        product_map = {p.id: p for p in products}

        items = []
        for pid_str, qty_str in raw.items():
            pid = int(pid_str)
            qty = int(qty_str)
            product = product_map.get(pid)
            if not product:
                continue
            price = float(product.price)
            items.append(CartItemResponse(
                product_id=pid,
                product_name=product.name,
                quantity=qty,
                unit_price=price,
                subtotal=round(price * qty, 2),
            ))

        total = round(sum(i.subtotal for i in items), 2)
        return CartResponse(items=items, total=total, item_count=sum(i.quantity for i in items))

    async def add_item(self, user_id: int, data: CartItemAdd) -> CartResponse:
        product = await self.product_repo.get_by_id(data.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        inv = await self.inv_repo.get_by_product_id(data.product_id)
        if not inv or inv.available < data.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

        key = _cart_key(user_id)
        current_qty = int(await self.redis.hget(key, str(data.product_id)) or 0)
        await self.redis.hset(key, str(data.product_id), current_qty + data.quantity)
        await self.redis.expire(key, CART_TTL)
        return await self.get_cart(user_id)

    async def remove_item(self, user_id: int, product_id: int) -> CartResponse:
        await self.redis.hdel(_cart_key(user_id), str(product_id))
        return await self.get_cart(user_id)

    async def clear_cart(self, user_id: int) -> None:
        await self.redis.delete(_cart_key(user_id))

    async def get_raw_items(self, user_id: int) -> dict[int, int]:
        raw = await self.redis.hgetall(_cart_key(user_id))
        return {int(k): int(v) for k, v in raw.items()}
