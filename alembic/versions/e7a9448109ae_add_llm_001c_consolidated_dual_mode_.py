"""Add LLM-001C consolidated dual-mode support

Revision ID: e7a9448109ae
Revises: aa6f9db26736
Create Date: 2025-09-17 16:01:56.120246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a9448109ae'
down_revision: Union[str, Sequence[str], None] = 'aa6f9db26736'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for LLM-001C consolidated dual-mode support."""
    # Extend conversations table for dual-mode support
    op.add_column('conversations', sa.Column('workflow_mode', sa.String(20), server_default='workbench'))
    op.add_column('conversations', sa.Column('business_context', sa.JSON, nullable=True))
    op.add_column('conversations', sa.Column('seo_metadata', sa.JSON, nullable=True))
    
    # Create business_profiles table
    op.create_table('business_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('website_url', sa.String(255), nullable=False),
        sa.Column('business_type', sa.String(100), nullable=False),
        sa.Column('target_market', sa.String(100), server_default='Nederland'),
        sa.Column('seo_experience_level', sa.String(50), server_default='beginner'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Create workflow_executions table
    op.create_table('workflow_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('workflow_mode', sa.String(20), nullable=False),
        sa.Column('execution_steps', sa.JSON),
        sa.Column('execution_successful', sa.Boolean, server_default=sa.text('true')),
        sa.Column('error_details', sa.Text, nullable=True),
        sa.Column('execution_duration_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Add indexes for performance
    op.create_index('idx_conversations_workflow_mode', 'conversations', ['workflow_mode'])
    op.create_index('idx_business_profiles_conversation', 'business_profiles', ['conversation_id'])
    op.create_index('idx_workflow_executions_conversation', 'workflow_executions', ['conversation_id'])
    op.create_index('idx_workflow_executions_mode', 'workflow_executions', ['workflow_mode'])


def downgrade() -> None:
    """Downgrade schema for LLM-001C consolidated dual-mode support."""
    # Remove indexes
    op.drop_index('idx_workflow_executions_mode')
    op.drop_index('idx_workflow_executions_conversation')
    op.drop_index('idx_business_profiles_conversation')
    op.drop_index('idx_conversations_workflow_mode')
    
    # Drop tables
    op.drop_table('workflow_executions')
    op.drop_table('business_profiles')
    
    # Remove columns from conversations
    op.drop_column('conversations', 'seo_metadata')
    op.drop_column('conversations', 'business_context')
    op.drop_column('conversations', 'workflow_mode')
