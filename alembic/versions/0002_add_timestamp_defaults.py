"""add server defaults to timestamp columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "tenants",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "tenants",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "documents",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "documents",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "document_chunks",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )

    op.alter_column(
        "document_chunks",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "document_chunks",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "document_chunks",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "documents",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "documents",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "users",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "tenants",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "tenants",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )