"""oauth_tokens table

Revision ID: 0011_oauth_tokens
Revises: 0010_integrations
Create Date: 2026-07-04

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_oauth_tokens"
down_revision: str | None = "0010_integrations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("account_email", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "provider", name="uq_oauth_tokens_scope"),
    )
    op.create_index("idx_oauth_tokens_lookup", "oauth_tokens", ["tenant_id", "user_id", "provider"])


def downgrade() -> None:
    op.drop_index("idx_oauth_tokens_lookup", table_name="oauth_tokens")
    op.drop_table("oauth_tokens")
