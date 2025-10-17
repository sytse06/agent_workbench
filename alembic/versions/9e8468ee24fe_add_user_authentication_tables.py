"""add_user_authentication_tables

Revision ID: 9e8468ee24fe
Revises: ca1c1d0b76c0
Create Date: 2025-10-14 16:14:27.233436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e8468ee24fe'
down_revision: Union[str, Sequence[str], None] = 'ca1c1d0b76c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user authentication tables (users, user_sessions, user_settings, session_activities)."""

    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('avatar_url', sa.String(1024), nullable=True),
        sa.Column('auth_provider', sa.String(50), nullable=False, server_default='huggingface', index=True),
        sa.Column('provider_data', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column('is_admin', sa.Boolean, nullable=False, server_default=sa.text('0')),
    )

    # 2. Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('referrer', sa.String(1024), nullable=True),
        sa.Column('total_messages', sa.Integer, nullable=False, server_default=sa.text('0')),
        sa.Column('total_tool_calls', sa.Integer, nullable=False, server_default=sa.text('0')),
    )

    # Add indexes for user_sessions
    op.create_index('idx_user_sessions_user_activity', 'user_sessions', ['user_id', 'last_activity'])
    op.create_index('idx_user_sessions_ended', 'user_sessions', ['ended_at'])

    # 3. Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('setting_key', sa.String(255), nullable=False, index=True),
        sa.Column('setting_value', sa.JSON, nullable=False),
        sa.Column('setting_type', sa.String(50), nullable=False, server_default='active'),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'setting_key', name='uq_user_settings_user_key'),
    )

    # Add indexes for user_settings
    op.create_index('idx_user_settings_category', 'user_settings', ['user_id', 'category'])

    # 4. Create session_activities table
    op.create_table(
        'session_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('user_sessions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Add indexes for session_activities
    op.create_index('idx_session_activities_session_time', 'session_activities', ['session_id', 'timestamp'])
    op.create_index('idx_session_activities_user_time', 'session_activities', ['user_id', 'timestamp'])

    # 5. Add user_id foreign key to conversations table (optional, nullable)
    # Note: Skip if already exists (added in Phase 1)
    from alembic import context
    conn = context.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('conversations')]

    if 'user_id' not in columns:
        op.add_column('conversations', sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True))


def downgrade() -> None:
    """Remove user authentication tables."""

    # Remove in reverse order of creation to handle foreign key constraints

    # 1. Remove user_id from conversations
    op.drop_column('conversations', 'user_id')

    # 2. Drop session_activities table
    op.drop_index('idx_session_activities_user_time')
    op.drop_index('idx_session_activities_session_time')
    op.drop_table('session_activities')

    # 3. Drop user_settings table
    op.drop_index('idx_user_settings_category')
    op.drop_table('user_settings')

    # 4. Drop user_sessions table
    op.drop_index('idx_user_sessions_ended')
    op.drop_index('idx_user_sessions_user_activity')
    op.drop_table('user_sessions')

    # 5. Drop users table
    op.drop_table('users')
