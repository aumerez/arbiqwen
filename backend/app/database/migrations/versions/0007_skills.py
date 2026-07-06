"""tenant_skill_configs table

Revision ID: 0007_skills
Revises: 0006_agents
Create Date: 2026-07-04

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_skills"
down_revision: str | None = "0006_agents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_skill_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("skill_key", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "skill_key", name="uq_tenant_skill"),
    )
    op.create_index("idx_tenant_skill_configs_tenant_id", "tenant_skill_configs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("idx_tenant_skill_configs_tenant_id", table_name="tenant_skill_configs")
    op.drop_table("tenant_skill_configs")
