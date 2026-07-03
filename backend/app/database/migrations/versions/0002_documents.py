"""documents and document_chunks tables

Revision ID: 0002_documents
Revises: 0001_auth_tables
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_documents"
down_revision: Union[str, None] = "0001_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = sa.Enum("queued", "processing", "indexed", "error", name="document_status", native_enum=False)
_INDEX_MODE = sa.Enum("full", "stub", "none", name="document_index_mode", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("mimetype", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("status", _STATUS, nullable=False),
        sa.Column("index_mode", _INDEX_MODE, server_default="full", nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("doc_title", sa.String(), nullable=True),
        sa.Column("authored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("folder_path", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_documents_user_id", "documents", ["user_id"])
    op.create_index("idx_documents_status", "documents", ["status"])
    op.create_index("idx_documents_folder_path", "documents", ["folder_path"])
    op.create_index("idx_documents_source_external_id", "documents", ["source", "external_id"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), server_default="1", nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_document_chunks_document_id", "document_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_index("idx_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("idx_documents_source_external_id", table_name="documents")
    op.drop_index("idx_documents_folder_path", table_name="documents")
    op.drop_index("idx_documents_status", table_name="documents")
    op.drop_index("idx_documents_user_id", table_name="documents")
    op.drop_table("documents")
