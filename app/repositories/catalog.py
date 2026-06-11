from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.catalog import Category, Product


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[Category]:
        result = await self.db.execute(
            select(Category).where(Category.is_active == True).order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, name: str, slug: str, description: str | None) -> Category:
        category = Category(name=name, slug=slug, description=description)
        self.db.add(category)
        await self.db.flush()
        return category


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, category_id: int | None = None) -> list[Product]:
        query = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.is_active == True)
        )
        if category_id:
            query = query.where(Product.category_id == category_id)
        result = await self.db.execute(query)
        return list(result.unique().scalars().all())

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.id == product_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_by_ids(self, product_ids: list[int]) -> list[Product]:
        result = await self.db.execute(
            select(Product)
            .options(joinedload(Product.inventory))
            .where(Product.id.in_(product_ids))
        )
        return list(result.unique().scalars().all())

    async def create(self, **kwargs) -> Product:
        product = Product(**kwargs)
        self.db.add(product)
        await self.db.flush()
        return product
