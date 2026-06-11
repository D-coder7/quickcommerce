from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import get_admin_user
from app.schemas.catalog import CategoryCreate, CategoryResponse, ProductCreate, ProductDetailResponse
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = CatalogService(db, redis)
    return await service.get_categories()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(get_admin_user),
):
    service = CatalogService(db, redis)
    return await service.create_category(data)


@router.get("/products", response_model=list[ProductDetailResponse])
async def list_products(
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = CatalogService(db, redis)
    return await service.get_products(category_id=category_id)


@router.post("/products", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    _=Depends(get_admin_user),
):
    service = CatalogService(db, redis)
    return await service.create_product(data)
