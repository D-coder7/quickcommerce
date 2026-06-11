from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_current_user
from app.schemas.cart import CartItemAdd, CartResponse
from app.services.cart import CartService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await CartService(db, redis).get_cart(current_user.id)


@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await CartService(db, redis).add_item(current_user.id, data)


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await CartService(db, redis).remove_item(current_user.id, product_id)


@router.delete("/", status_code=204)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    await CartService(db, redis).clear_cart(current_user.id)
