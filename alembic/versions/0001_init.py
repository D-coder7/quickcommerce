"""init

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum type ────────────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE orderstatus AS ENUM (
                'pending','confirmed','preparing',
                'out_for_delivery','delivered','cancelled'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$
    """)
    # ── users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",              sa.Integer(),     nullable=False),
        sa.Column("email",           sa.String(255),   nullable=False),
        sa.Column("hashed_password", sa.String(255),   nullable=False),
        sa.Column("full_name",       sa.String(255),   nullable=False),
        sa.Column("phone",           sa.String(20),    nullable=True),
        sa.Column("is_active",       sa.Boolean(),     nullable=False, server_default=sa.true()),
        sa.Column("is_admin",        sa.Boolean(),     nullable=False, server_default=sa.false()),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",      sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("ix_users_id",    "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ── categories ───────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id",          sa.Integer(),   nullable=False),
        sa.Column("name",        sa.String(100), nullable=False),
        sa.Column("slug",        sa.String(100), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        sa.Column("is_active",   sa.Boolean(),   nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_categories_id",   "categories", ["id"])
    op.create_index("ix_categories_slug", "categories", ["slug"])

    # ── products ─────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id",          sa.Integer(),      nullable=False),
        sa.Column("category_id", sa.Integer(),      nullable=False),
        sa.Column("name",        sa.String(255),    nullable=False),
        sa.Column("slug",        sa.String(255),    nullable=False),
        sa.Column("description", sa.Text(),         nullable=True),
        sa.Column("price",       sa.Numeric(10, 2), nullable=False),
        sa.Column("image_url",   sa.String(500),    nullable=True),
        sa.Column("is_active",   sa.Boolean(),      nullable=False, server_default=sa.true()),
        sa.Column("created_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",  sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_products_id",          "products", ["id"])
    op.create_index("ix_products_slug",        "products", ["slug"])
    op.create_index("ix_products_category_id", "products", ["category_id"])

    # ── inventory ────────────────────────────────────────────────────────
    op.create_table(
        "inventory",
        sa.Column("id",         sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity",   sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved",   sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )
    op.create_index("ix_inventory_id", "inventory", ["id"])

    # ── orders (raw SQL — avoids SQLAlchemy enum DDL hooks) ─────────────
    op.execute(sa.text("""
        CREATE TABLE orders (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER NOT NULL REFERENCES users(id),
            status           orderstatus NOT NULL DEFAULT 'pending',
            total_amount     NUMERIC(10,2) NOT NULL,
            delivery_address VARCHAR(500) NOT NULL,
            notes            VARCHAR(500),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))
    op.create_index("ix_orders_id",      "orders", ["id"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_status",  "orders", ["status"])

    # ── order_items ──────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id",         sa.Integer(),      nullable=False),
        sa.Column("order_id",   sa.Integer(),      nullable=False),
        sa.Column("product_id", sa.Integer(),      nullable=False),
        sa.Column("quantity",   sa.Integer(),      nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"],   ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_items_id",       "order_items", ["id"])
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("inventory")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("users")

    sa.Enum(name="orderstatus").drop(op.get_bind(), checkfirst=True)
