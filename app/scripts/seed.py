"""
Run with: docker compose exec api python -m app.scripts.seed
Idempotent — safe to run multiple times.
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.catalog import Category, Product
from app.models.inventory import Inventory

CATEGORIES = [
    {"name": "Fruits & Vegetables", "slug": "fruits-vegetables", "description": "Fresh produce"},
    {"name": "Dairy & Eggs",        "slug": "dairy-eggs",        "description": "Milk, cheese, eggs"},
    {"name": "Snacks",              "slug": "snacks",             "description": "Chips, biscuits, nuts"},
    {"name": "Beverages",           "slug": "beverages",          "description": "Juices, water, soft drinks"},
]

PRODUCTS = [
    # Fruits & Vegetables
    {"category_slug": "fruits-vegetables", "name": "Banana (dozen)",       "slug": "banana-dozen",       "price": 39.00,  "stock": 150},
    {"category_slug": "fruits-vegetables", "name": "Tomatoes (500g)",      "slug": "tomatoes-500g",      "price": 25.00,  "stock": 200},
    {"category_slug": "fruits-vegetables", "name": "Spinach (200g)",       "slug": "spinach-200g",       "price": 18.00,  "stock": 80},
    {"category_slug": "fruits-vegetables", "name": "Onions (1kg)",         "slug": "onions-1kg",         "price": 32.00,  "stock": 300},
    {"category_slug": "fruits-vegetables", "name": "Apples Royal Gala (4)","slug": "apples-royal-gala-4","price": 89.00,  "stock": 120},
    # Dairy & Eggs
    {"category_slug": "dairy-eggs",        "name": "Full Cream Milk (1L)", "slug": "full-cream-milk-1l", "price": 72.00,  "stock": 100},
    {"category_slug": "dairy-eggs",        "name": "Eggs (12 pack)",       "slug": "eggs-12-pack",       "price": 95.00,  "stock": 90},
    {"category_slug": "dairy-eggs",        "name": "Paneer (200g)",        "slug": "paneer-200g",        "price": 60.00,  "stock": 60},
    {"category_slug": "dairy-eggs",        "name": "Curd (400g)",          "slug": "curd-400g",          "price": 42.00,  "stock": 75},
    # Snacks
    {"category_slug": "snacks",            "name": "Lay's Classic (52g)",  "slug": "lays-classic-52g",   "price": 20.00,  "stock": 500},
    {"category_slug": "snacks",            "name": "Digestive Biscuits",   "slug": "digestive-biscuits", "price": 55.00,  "stock": 250},
    {"category_slug": "snacks",            "name": "Mixed Nuts (100g)",    "slug": "mixed-nuts-100g",    "price": 120.00, "stock": 70},
    # Beverages
    {"category_slug": "beverages",         "name": "Mineral Water (1L)",   "slug": "mineral-water-1l",   "price": 20.00,  "stock": 400},
    {"category_slug": "beverages",         "name": "Orange Juice (1L)",    "slug": "orange-juice-1l",    "price": 99.00,  "stock": 80},
    {"category_slug": "beverages",         "name": "Cola (2L)",            "slug": "cola-2l",            "price": 65.00,  "stock": 150},
]

ADMIN = {
    "email":       "admin@quickcommerce.dev",
    "password":    "Admin@1234",
    "full_name":   "Super Admin",
    "is_admin":    True,
}

DEMO_USER = {
    "email":       "user@quickcommerce.dev",
    "password":    "User@1234",
    "full_name":   "Demo User",
    "is_admin":    False,
}


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # ── Users ────────────────────────────────────────────────────────
        for spec in (ADMIN, DEMO_USER):
            existing = (await db.execute(select(User).where(User.email == spec["email"]))).scalar_one_or_none()
            if not existing:
                db.add(User(
                    email=spec["email"],
                    hashed_password=hash_password(spec["password"]),
                    full_name=spec["full_name"],
                    is_admin=spec["is_admin"],
                ))
                print(f"  created user: {spec['email']}")
            else:
                print(f"  skip user (exists): {spec['email']}")
        await db.flush()

        # ── Categories ───────────────────────────────────────────────────
        category_map: dict[str, int] = {}
        for spec in CATEGORIES:
            existing = (await db.execute(select(Category).where(Category.slug == spec["slug"]))).scalar_one_or_none()
            if not existing:
                cat = Category(name=spec["name"], slug=spec["slug"], description=spec["description"])
                db.add(cat)
                await db.flush()
                category_map[spec["slug"]] = cat.id
                print(f"  created category: {spec['name']}")
            else:
                category_map[spec["slug"]] = existing.id
                print(f"  skip category (exists): {spec['name']}")

        # ── Products + Inventory ─────────────────────────────────────────
        for spec in PRODUCTS:
            existing = (await db.execute(select(Product).where(Product.slug == spec["slug"]))).scalar_one_or_none()
            if not existing:
                product = Product(
                    category_id=category_map[spec["category_slug"]],
                    name=spec["name"],
                    slug=spec["slug"],
                    price=spec["price"],
                )
                db.add(product)
                await db.flush()

                db.add(Inventory(product_id=product.id, quantity=spec["stock"]))
                print(f"  created product: {spec['name']}  (stock={spec['stock']})")
            else:
                inv = (await db.execute(select(Inventory).where(Inventory.product_id == existing.id))).scalar_one_or_none()
                if not inv:
                    db.add(Inventory(product_id=existing.id, quantity=spec["stock"]))
                    print(f"  added inventory for existing product: {spec['name']}")
                else:
                    print(f"  skip product (exists): {spec['name']}")

        await db.commit()
        print("\nSeed complete.")
        print(f"  Admin login : {ADMIN['email']} / {ADMIN['password']}")
        print(f"  User login  : {DEMO_USER['email']} / {DEMO_USER['password']}")


if __name__ == "__main__":
    asyncio.run(seed())
