"""artifacts and dashboards tables

Revision ID: 0009_dashboards
Revises: 0008_playbooks
Create Date: 2026-07-04

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_dashboards"
down_revision: str | None = "0008_playbooks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("skill_key", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("container", sa.String(), nullable=True),
        sa.Column("item_id", sa.String(), nullable=True),
        sa.Column("trust_level", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_artifacts_chat_id", "artifacts", ["chat_id"])

    op.create_table(
        "dashboards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("sample_data", sa.JSON(), nullable=True),
        sa.Column("sections", sa.JSON(), nullable=True),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("source_chat_id", sa.Integer(), nullable=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_chat_id"], ["chats.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_dashboards_project_id", "dashboards", ["project_id"])
    op.create_index("idx_dashboards_created_by_user_id", "dashboards", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("idx_dashboards_created_by_user_id", table_name="dashboards")
    op.drop_index("idx_dashboards_project_id", table_name="dashboards")
    op.drop_table("dashboards")
    op.drop_index("idx_artifacts_chat_id", table_name="artifacts")
    op.drop_table("artifacts")
