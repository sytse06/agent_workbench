"""add_thread_metadata_rename_fks_drop_conversations

Revision ID: 4ea9663c23e2
Revises: bbcc45c43561
Create Date: 2026-03-19 18:20:43.465059

PR-2.6a: Adds thread_metadata table for the conversation browser.
The LangGraph checkpointer is now the single source of truth for conversation
state; this table stores only the human-readable metadata needed for listing.

Documents still reference conversations.id via conversation_id (thread_id
semantically). The FK rename and conversations table drop will follow in a
subsequent migration once the sidebar UI is live and threads are listed.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ea9663c23e2"
down_revision: Union[str, Sequence[str], None] = "bbcc45c43561"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "thread_metadata",
        sa.Column("thread_id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("preview", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_thread_metadata_last_updated",
        "thread_metadata",
        ["last_updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_thread_metadata_last_updated", table_name="thread_metadata")
    op.drop_table("thread_metadata")
