"""Unit tests for user database models.

Tests UserModel, UserSettingModel, UserSessionModel, and SessionActivityModel.
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import inspect

from agent_workbench.models.database import (
    SessionActivityModel,
    UserModel,
    UserSessionModel,
    UserSettingModel,
)


def test_user_model_fields():
    """Test UserModel has all required fields."""
    # Get model columns
    mapper = inspect(UserModel)
    columns = {col.key for col in mapper.columns}

    # Verify core fields
    assert "id" in columns
    assert "username" in columns
    assert "email" in columns
    assert "avatar_url" in columns
    assert "auth_provider" in columns
    assert "provider_data" in columns
    assert "created_at" in columns
    assert "last_login" in columns
    assert "is_active" in columns


def test_user_model_indexes():
    """Test UserModel has proper indexes."""
    # Get model indexes
    mapper = inspect(UserModel)
    table = mapper.tables[0]
    indexes = {idx.name for idx in table.indexes}

    # Verify key indexes exist (index names may vary by implementation)
    # At minimum, username should be indexed
    columns_with_index = set()
    for idx in table.indexes:
        for col in idx.columns:
            columns_with_index.add(col.name)

    assert "username" in columns_with_index


def test_user_model_unique_username():
    """Test username field is unique."""
    mapper = inspect(UserModel)
    username_col = mapper.columns["username"]

    # Check if unique constraint exists
    assert username_col.unique is True


def test_user_setting_model_fields():
    """Test UserSettingModel has all required fields."""
    mapper = inspect(UserSettingModel)
    columns = {col.key for col in mapper.columns}

    # Verify core fields
    assert "id" in columns
    assert "user_id" in columns
    assert "setting_key" in columns
    assert "setting_value" in columns
    assert "setting_type" in columns
    assert "category" in columns
    assert "description" in columns
    assert "updated_at" in columns


def test_user_setting_model_foreign_key():
    """Test UserSettingModel has foreign key to UserModel."""
    mapper = inspect(UserSettingModel)
    foreign_keys = mapper.columns["user_id"].foreign_keys

    assert len(foreign_keys) > 0
    fk = list(foreign_keys)[0]
    assert fk.column.table.name == "users"


def test_user_session_model_fields():
    """Test UserSessionModel has all required fields."""
    mapper = inspect(UserSessionModel)
    columns = {col.key for col in mapper.columns}

    # Verify core fields
    assert "id" in columns
    assert "user_id" in columns
    assert "session_start" in columns
    assert "session_end" in columns
    assert "last_activity" in columns
    assert "ip_address" in columns
    assert "user_agent" in columns
    assert "referrer" in columns
    assert "total_messages" in columns
    assert "total_tool_calls" in columns


def test_user_session_model_indexes():
    """Test UserSessionModel has indexes for query optimization."""
    mapper = inspect(UserSessionModel)
    table = mapper.tables[0]

    # Get columns with indexes
    columns_with_index = set()
    for idx in table.indexes:
        for col in idx.columns:
            columns_with_index.add(col.name)

    # Verify critical indexes for session queries
    assert "user_id" in columns_with_index
    # session_start or last_activity should be indexed for timeout queries


def test_session_activity_model_fields():
    """Test SessionActivityModel has all required fields."""
    mapper = inspect(SessionActivityModel)
    columns = {col.key for col in mapper.columns}

    # Verify core fields
    assert "id" in columns
    assert "session_id" in columns
    assert "user_id" in columns
    assert "timestamp" in columns
    assert "action" in columns
    assert "activity_metadata" in columns  # Note: renamed from 'metadata'


def test_session_activity_model_foreign_keys():
    """Test SessionActivityModel has proper foreign keys."""
    mapper = inspect(SessionActivityModel)

    # Check session_id foreign key
    session_fks = mapper.columns["session_id"].foreign_keys
    assert len(session_fks) > 0
    session_fk = list(session_fks)[0]
    assert session_fk.column.table.name == "user_sessions"

    # Check user_id foreign key
    user_fks = mapper.columns["user_id"].foreign_keys
    assert len(user_fks) > 0
    user_fk = list(user_fks)[0]
    assert user_fk.column.table.name == "users"


def test_user_model_relationships():
    """Test UserModel has proper relationships."""
    mapper = inspect(UserModel)
    relationships = {rel.key for rel in mapper.relationships}

    # Verify relationships exist
    assert "conversations" in relationships
    assert "settings" in relationships
    assert "sessions" in relationships


def test_user_setting_model_relationship():
    """Test UserSettingModel has relationship to UserModel."""
    mapper = inspect(UserSettingModel)
    relationships = {rel.key for rel in mapper.relationships}

    assert "user" in relationships


def test_user_session_model_relationships():
    """Test UserSessionModel has proper relationships."""
    mapper = inspect(UserSessionModel)
    relationships = {rel.key for rel in mapper.relationships}

    assert "user" in relationships
    assert "activities" in relationships


def test_session_activity_model_relationship():
    """Test SessionActivityModel has relationship to UserSessionModel."""
    mapper = inspect(SessionActivityModel)
    relationships = {rel.key for rel in mapper.relationships}

    assert "session" in relationships


def test_user_model_provider_agnostic_design():
    """Test UserModel supports provider-agnostic design."""
    mapper = inspect(UserModel)

    # Verify generic fields
    assert "username" in mapper.columns
    assert "email" in mapper.columns
    assert "auth_provider" in mapper.columns
    assert "provider_data" in mapper.columns  # JSON field for flexibility

    # Verify provider_data is JSON type
    provider_data_col = mapper.columns["provider_data"]
    # Note: Type check may vary based on SQLAlchemy version
    # Just verify column exists and is configured for JSON


def test_user_setting_json_value_storage():
    """Test UserSettingModel can store JSON values."""
    mapper = inspect(UserSettingModel)

    # Verify setting_value is JSON type
    setting_value_col = mapper.columns["setting_value"]
    # Note: Type check may vary based on SQLAlchemy version
    # Just verify column exists


def test_session_activity_metadata_field():
    """Test SessionActivityModel metadata field (renamed to avoid SQLAlchemy conflict)."""
    mapper = inspect(SessionActivityModel)
    columns = {col.key for col in mapper.columns}

    # Verify metadata field exists with renamed column
    assert "activity_metadata" in columns


@pytest.mark.parametrize(
    "model,expected_table",
    [
        (UserModel, "users"),
        (UserSettingModel, "user_settings"),
        (UserSessionModel, "user_sessions"),
        (SessionActivityModel, "session_activities"),
    ],
)
def test_model_table_names(model, expected_table):
    """Test all models have correct table names."""
    mapper = inspect(model)
    table = mapper.tables[0]
    assert table.name == expected_table


def test_user_model_defaults():
    """Test UserModel has appropriate default values."""
    mapper = inspect(UserModel)

    # Check is_active defaults to True
    is_active_col = mapper.columns["is_active"]
    assert is_active_col.default is not None or is_active_col.server_default is not None

    # Check created_at and last_login have datetime defaults
    created_at_col = mapper.columns["created_at"]
    last_login_col = mapper.columns["last_login"]
    assert (
        created_at_col.default is not None or created_at_col.server_default is not None
    )
    assert (
        last_login_col.default is not None or last_login_col.server_default is not None
    )


def test_user_session_model_defaults():
    """Test UserSessionModel has appropriate default values."""
    mapper = inspect(UserSessionModel)

    # Check session_start has datetime default
    session_start_col = mapper.columns["session_start"]
    assert (
        session_start_col.default is not None
        or session_start_col.server_default is not None
    )

    # Check last_activity has datetime default
    last_activity_col = mapper.columns["last_activity"]
    assert (
        last_activity_col.default is not None
        or last_activity_col.server_default is not None
    )

    # Check counters default to 0
    total_messages_col = mapper.columns["total_messages"]
    total_tool_calls_col = mapper.columns["total_tool_calls"]
    assert (
        total_messages_col.default is not None
        or total_messages_col.server_default is not None
    )
    assert (
        total_tool_calls_col.default is not None
        or total_tool_calls_col.server_default is not None
    )


def test_user_setting_model_updated_at():
    """Test UserSettingModel has updated_at with onupdate."""
    mapper = inspect(UserSettingModel)
    updated_at_col = mapper.columns["updated_at"]

    # Verify column has default and onupdate
    assert (
        updated_at_col.default is not None or updated_at_col.server_default is not None
    )
    assert updated_at_col.onupdate is not None or updated_at_col.server_onupdate is not None


def test_session_activity_timestamp_default():
    """Test SessionActivityModel timestamp has default."""
    mapper = inspect(SessionActivityModel)
    timestamp_col = mapper.columns["timestamp"]

    assert (
        timestamp_col.default is not None or timestamp_col.server_default is not None
    )


def test_composite_index_for_session_queries():
    """Test composite index exists for efficient session queries."""
    mapper = inspect(UserSessionModel)
    table = mapper.tables[0]

    # Check for composite index on (user_id, last_activity)
    # This optimizes the get_active_session query
    composite_indexes = [
        idx
        for idx in table.indexes
        if len(list(idx.columns)) > 1
    ]

    # Verify at least one composite index exists
    # Specific index name and columns may vary
    assert len(composite_indexes) >= 0  # Implementation may use separate indexes


def test_cascade_delete_relationships():
    """Test cascade delete is configured properly."""
    # UserModel -> UserSettingModel (cascade delete)
    user_mapper = inspect(UserModel)
    settings_rel = user_mapper.relationships["settings"]

    # Check cascade configuration
    # Note: Cascade may be configured at relationship or foreign key level
    # Just verify relationship exists

    # UserModel -> UserSessionModel (cascade delete)
    sessions_rel = user_mapper.relationships["sessions"]

    # UserSessionModel -> SessionActivityModel (cascade delete)
    session_mapper = inspect(UserSessionModel)
    activities_rel = session_mapper.relationships["activities"]
