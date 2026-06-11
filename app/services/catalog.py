import json
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.repositories.catalog import CategoryRepository, ProductRepository
from app.repositories.inventory import InventoryRepository
from app.schemas.catalog import CategoryCreate, ProductCreate, ProductDetailResponse
from app.core.config import get_settings

settings = get_settings()

PRODUCTS_CACHE_KEY = "catalog:products"
CATEGORIES_CACHE_KEY = "catalog:categories"


class CatalogService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.category_repo = CategoryRepository(db)
        self.product_repo = ProductRepository(db)
        self.inv_repo = InventoryRepository(db)
        self.redis = redis

    async def get_categories(self) -> list:
        cached = await self.redis.get(CATEGORIES_CACHE_KEY)
        if cached:
            return json.loads(cached)

        categories = await self.category_repo.get_all()
        data = [{"id": c.id, "name": c.name, "slug": c.slug, "description": c.description} for c in categories]
        await self.redis.setex(CATEGORIES_CACHE_KEY, settings.catalog_cache_ttl, json.dumps(data))
        return data

    async def get_products(self, category_id: int | None = None) -> list[ProductDetailResponse]:
        cache_key = f"{PRODUCTS_CACHE_KEY}:{category_id or 'all'}"
        cached = await self.redis.get(cache_key)
        if cached:
            return [ProductDetailResponse.model_validate(p) for p in json.loads(cached)]

        products = await self.product_repo.get_all(category_id=category_id)
        result = []
        for p in products:
            detail = ProductDetailResponse.model_validate({
                "id": p.id,
                "category_id": p.category_id,
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "price": float(p.price),
                "image_url": p.image_url,
                "is_active": p.is_active,
                "category": p.category,
                "available_quantity": p.inventory.available if p.inventory else 0,
            })
            result.append(detail)

        await self.redis.setex(
            cache_key,
            settings.catalog_cache_ttl,
            json.dumps([r.model_dump() for r in result]),
        )
        return result

    async def invalidate_cache(self) -> None:
        keys = await self.redis.keys("catalog:*")
        if keys:
            await self.redis.delete(*keys)

    async def create_category(self, data: CategoryCreate):
        existing = await self.category_repo.get_by_slug(data.slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
        category = await self.category_repo.create(data.name, data.slug, data.description)
        await self.invalidate_cache()
        return category

    async def create_product(self, data: ProductCreate):
        product = await self.product_repo.create(**data.model_dump())
        await self.invalidate_cache()
        return product
