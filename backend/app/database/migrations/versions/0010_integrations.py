"""integrations and integration_connections tables

Revision ID: 0010_integrations
Revises: 0009_dashboards
Create Date: 2026-07-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0010_integrations"
down_revision: Union[str, None] = "0009_dashboards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("instance_alias", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("icon_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "instance_alias", name="uq_integration_tenant_alias"),
    )
    op.create_index("idx_integrations_category", "integrations", ["category"])
    op.create_index("idx_integrations_status", "integrations", ["status"])

    op.create_table(
        "integration_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("integration_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_integration_connections_integration_id", "integration_connections", ["integration_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_integration_connections_integration_id", table_name="integration_connections")
    op.drop_table("integration_connections")
    op.drop_index("idx_integrations_status", table_name="integrations")
    op.drop_index("idx_integrations_category", table_name="integrations")
    op.drop_table("integrations")
