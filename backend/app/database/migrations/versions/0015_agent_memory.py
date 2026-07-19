"""agent_memories table

Revision ID: 0015_agent_memory
Revises: 0014_agent_checkpoint
Create Date: 2026-07-07

Stores memory records written at the end of each agent run so subsequent runs
can recall relevant past outcomes and inject them into the system prompt.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_agent_memory"
down_revision: str | None = "0014_agent_checkpoint"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, index=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("definition_id", sa.Integer(), sa.ForeignKey("agent_definitions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("qdrant_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("agent_memories")
