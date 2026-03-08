"""add_documents_tables

Revision ID: bbcc45c43561
Revises: 9e8468ee24fe
Create Date: 2026-03-08 16:55:22.612202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbcc45c43561'
down_revision: Union[str, Sequence[str], None] = '9e8468ee24fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="processed"
        ),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("total_tokens", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_documents_conversation_id", "documents", ["conversation_id"]
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("heading", sa.Text, nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=False),
    )
    op.create_index(
        "idx_document_chunks_document_id", "document_chunks", ["document_id"]
    )
    op.create_index(
        "idx_document_chunks_order",
        "document_chunks",
        ["document_id", "chunk_index"],
    )


def downgrade() -> None:
    op.drop_index("idx_document_chunks_order", table_name="document_chunks")
    op.drop_index("idx_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("idx_documents_conversation_id", table_name="documents")
    op.drop_table("documents")
