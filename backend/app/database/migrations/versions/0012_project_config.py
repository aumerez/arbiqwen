"""project_rag_sources and project_integrations tables

Revision ID: 0012_project_config
Revises: 0011_oauth_tokens
Create Date: 2026-07-05

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_project_config"
down_revision: str | None = "0011_oauth_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_rag_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("rag_source_id", sa.Integer(), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rag_source_id"], ["tenant_rag_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "rag_source_id", name="uq_project_rag_source"),
    )
    op.create_index("idx_project_rag_sources_project_id", "project_rag_sources", ["project_id"])

    op.create_table(
        "project_integrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=True),
        sa.Column("integration_key", sa.String(), nullable=True),
        sa.Column("enabled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_project_integrations_project_id", "project_integrations", ["project_id"])
    op.create_index(
        "uq_project_integration_id",
        "project_integrations",
        ["project_id", "integration_id"],
        unique=True,
        sqlite_where=sa.text("integration_id IS NOT NULL"),
        postgresql_where=sa.text("integration_id IS NOT NULL"),
    )
    op.create_index(
        "uq_project_integration_key",
        "project_integrations",
        ["project_id", "integration_key"],
        unique=True,
        sqlite_where=sa.text("integration_key IS NOT NULL"),
        postgresql_where=sa.text("integration_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_project_integration_key", table_name="project_integrations")
    op.drop_index("uq_project_integration_id", table_name="project_integrations")
    op.drop_index("idx_project_integrations_project_id", table_name="project_integrations")
    op.drop_table("project_integrations")
    op.drop_index("idx_project_rag_sources_project_id", table_name="project_rag_sources")
    op.drop_table("project_rag_sources")
