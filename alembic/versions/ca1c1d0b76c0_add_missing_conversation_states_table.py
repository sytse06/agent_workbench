"""Add missing conversation_states table

Revision ID: ca1c1d0b76c0
Revises: e7a9448109ae
Create Date: 2025-09-23 15:00:01.339799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca1c1d0b76c0'
down_revision: Union[str, Sequence[str], None] = 'e7a9448109ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing conversation_states table."""
    op.create_table('conversation_states',
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id'), primary_key=True),
        sa.Column('state_data', sa.JSON, nullable=False),
        sa.Column('context_data', sa.JSON, nullable=True),
        sa.Column('active_contexts', sa.JSON, nullable=True),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('version', sa.Integer, server_default=sa.text('1')),
    )

    # Add indexes for performance
    op.create_index('idx_conversation_states_updated', 'conversation_states', ['updated_at'])


def downgrade() -> None:
    """Remove conversation_states table."""
    op.drop_index('idx_conversation_states_updated')
    op.drop_table('conversation_states')
