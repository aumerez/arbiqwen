"""agent_runs: human-in-the-loop checkpoint columns

Revision ID: 0014_agent_checkpoint
Revises: 0013_agent_model_split
Create Date: 2026-07-07

Adds pending_action (the proposed write awaiting approval) and messages (the
serialized conversation, persisted so approve/reject can resume the loop) to
agent_runs. The waiting_approval / rejected statuses are plain string values —
no schema change.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014_agent_checkpoint"
down_revision: str | None = "0013_agent_model_split"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("pending_action", sa.JSON(), nullable=True))
    op.add_column("agent_runs", sa.Column("messages", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_runs", "messages")
    op.drop_column("agent_runs", "pending_action")
