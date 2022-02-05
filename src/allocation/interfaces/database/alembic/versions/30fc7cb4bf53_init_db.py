"""Init DB

Revision ID: 30fc7cb4bf53
Revises:
Create Date: 2022-01-23 14:41:50.547098

"""
from alembic import op
import sqlalchemy as sa
import allocation.interfaces.database.datatypes


# revision identifiers, used by Alembic.
revision = "30fc7cb4bf53"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "customers",
        sa.Column(
            "uuid", allocation.interfaces.database.datatypes.GUID(), nullable=False
        ),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_table(
        "skus",
        sa.Column(
            "uuid", allocation.interfaces.database.datatypes.GUID(), nullable=False
        ),
        sa.Column("cname", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_table(
        "orders",
        sa.Column(
            "uuid", allocation.interfaces.database.datatypes.GUID(), nullable=False
        ),
        sa.Column("order_items", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["uuid"],
            ["skus.uuid"],
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_table(
        "products",
        sa.Column(
            "_sku_id", allocation.interfaces.database.datatypes.GUID(), nullable=False
        ),
        sa.Column("version_number", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_sku_id"],
            ["skus.uuid"],
        ),
        sa.PrimaryKeyConstraint("_sku_id"),
    )
    op.create_table(
        "batches",
        sa.Column(
            "uuid", allocation.interfaces.database.datatypes.GUID(), nullable=False
        ),
        sa.Column(
            "_sku_id", allocation.interfaces.database.datatypes.GUID(), nullable=True
        ),
        sa.Column(
            "_product_id",
            allocation.interfaces.database.datatypes.GUID(),
            nullable=True,
        ),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("eta", sa.Date(), nullable=True),
        sa.Column("allocated_quantity", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_product_id"],
            ["products._sku_id"],
        ),
        sa.ForeignKeyConstraint(
            ["_sku_id"],
            ["skus.uuid"],
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_table(
        "order_items",
        sa.Column(
            "uuid", allocation.interfaces.database.datatypes.GUID(), nullable=False
        ),
        sa.Column(
            "_sku_id", allocation.interfaces.database.datatypes.GUID(), nullable=True
        ),
        sa.Column(
            "_product_id",
            allocation.interfaces.database.datatypes.GUID(),
            nullable=True,
        ),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["_product_id"],
            ["products._sku_id"],
        ),
        sa.ForeignKeyConstraint(
            ["_sku_id"],
            ["skus.uuid"],
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_table(
        "association",
        sa.Column(
            "order_item_id",
            allocation.interfaces.database.datatypes.GUID(),
            nullable=True,
        ),
        sa.Column(
            "batches_id", allocation.interfaces.database.datatypes.GUID(), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["batches_id"],
            ["batches.uuid"],
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.uuid"],
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("association")
    op.drop_table("order_items")
    op.drop_table("batches")
    op.drop_table("products")
    op.drop_table("orders")
    op.drop_table("skus")
    op.drop_table("customers")
    # ### end Alembic commands ###
