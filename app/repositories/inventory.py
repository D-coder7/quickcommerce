from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.inventory import Inventory


class InventoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_product_id(self, product_id: int) -> Inventory | None:
        result = await self.db.execute(
            select(Inventory).where(Inventory.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_product_id_for_update(self, product_id: int) -> Inventory | None:
        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def upsert(self, product_id: int, quantity: int) -> Inventory:
        stmt = (
            pg_insert(Inventory)
            .values(product_id=product_id, quantity=quantity)
            .on_conflict_do_update(
                index_elements=["product_id"],
                set_={"quantity": quantity},
            )
            .returning(Inventory)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalar_one()

    async def reserve(self, product_id: int, quantity: int) -> bool:
        inv = await self.get_by_product_id_for_update(product_id)
        if not inv or inv.available < quantity:
            return False
        inv.reserved += quantity
        await self.db.flush()
        return True

    async def release_reservation(self, product_id: int, quantity: int) -> None:
        inv = await self.get_by_product_id_for_update(product_id)
        if inv:
            inv.reserved = max(0, inv.reserved - quantity)
            await self.db.flush()

    async def confirm_sale(self, product_id: int, quantity: int) -> None:
        inv = await self.get_by_product_id_for_update(product_id)
        if inv:
            inv.quantity -= quantity
            inv.reserved = max(0, inv.reserved - quantity)
            await self.db.flush()
