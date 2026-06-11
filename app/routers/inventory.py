from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_admin_user
from app.repositories.inventory import InventoryRepository
from app.services.catalog import CatalogService
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse

router = APIRouter()


@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def set_inventory(
    data: InventoryCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(get_admin_user),
):
    repo = InventoryRepository(db)
    inv = await repo.upsert(data.product_id, data.quantity)
    await CatalogService(db, redis).invalidate_cache()
    return inv


@router.patch("/{product_id}", response_model=InventoryResponse)
async def update_inventory(
    product_id: int,
    data: InventoryUpdate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(get_admin_user),
):
    repo = InventoryRepository(db)
    inv = await repo.upsert(product_id, data.quantity)
    await CatalogService(db, redis).invalidate_cache()
    return inv


@router.get("/{product_id}", response_model=InventoryResponse)
async def get_inventory(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_admin_user),
):
    repo = InventoryRepository(db)
    inv = await repo.get_by_product_id(product_id)
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    return inv
