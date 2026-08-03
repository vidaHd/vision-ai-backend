"""add users and restaurant ownership

Revision ID: 002_users_owner
Revises: 001_create_restaurants
Create Date: 2026-07-31 11:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_users_owner"
down_revision: Union[str, Sequence[str], None] = "001_create_restaurants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Existing restaurants cannot be owned; clear them before requiring user_id.
    op.execute(sa.text("DELETE FROM restaurants"))

    op.add_column(
        "restaurants",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index(
        op.f("ix_restaurants_user_id"),
        "restaurants",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_restaurants_user_id_users"),
        "restaurants",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_restaurants_user_id_users"),
        "restaurants",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_restaurants_user_id"), table_name="restaurants")
    op.drop_column("restaurants", "user_id")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
