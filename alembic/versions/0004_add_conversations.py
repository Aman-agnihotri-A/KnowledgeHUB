"""add conversation persistence

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


message_role = postgresql.ENUM(
    "USER",
    "ASSISTANT",
    name="messagerole",
)

message_role_column = postgresql.ENUM(
    "USER",
    "ASSISTANT",
    name="messagerole",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_conversations_tenant_id",
        "conversations",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        "ix_conversations_user_id",
        "conversations",
        ["user_id"],
        unique=False,
    )

    message_role.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
    "conversation_messages",
    sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        nullable=False,
    ),
    sa.Column(
        "conversation_id",
        postgresql.UUID(as_uuid=True),
        nullable=False,
    ),
    sa.Column(
        "message_index",
        sa.Integer(),
        nullable=False,
    ),
    sa.Column(
        "role",
        message_role_column,
        nullable=False,
    ),
    sa.Column(
        "content",
        sa.Text(),
        nullable=False,
    ),
    sa.Column(
        "sources",
        postgresql.JSONB(),
        nullable=True,
    ),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
    sa.ForeignKeyConstraint(
        ["conversation_id"],
        ["conversations.id"],
        ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint(
        "conversation_id",
        "message_index",
        name="uq_conversation_message_index",
    ),
)

    op.create_index(
        "ix_conversation_messages_conversation_id",
        "conversation_messages",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_messages_conversation_id",
        table_name="conversation_messages",
    )

    op.drop_table("conversation_messages")

    message_role.drop(
        op.get_bind(),
        checkfirst=True,
    )

    op.drop_index(
        "ix_conversations_user_id",
        table_name="conversations",
    )

    op.drop_index(
        "ix_conversations_tenant_id",
        table_name="conversations",
    )

    op.drop_table("conversations")