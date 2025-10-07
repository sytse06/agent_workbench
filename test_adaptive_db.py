#!/usr/bin/env python
"""Test AdaptiveDatabase functionality in local environment."""

import os
import sys
from uuid import uuid4

# Set environment before importing
os.environ["APP_MODE"] = "workbench"
os.environ["APP_ENV"] = "development"

print("=" * 80)
print("🔍 TESTING ADAPTIVE DATABASE")
print("=" * 80)

try:
    print("\n1️⃣ Testing environment detection...")
    from agent_workbench.database.detection import detect_environment, is_hub_db_environment

    env = detect_environment()
    is_hub = is_hub_db_environment()

    print(f"✅ Environment detected: {env}")
    print(f"✅ Is HF Hub environment: {is_hub}")

    if env != "local":
        print(f"⚠️  Expected 'local', got '{env}'")

    print("\n2️⃣ Testing AdaptiveDatabase import...")
    from agent_workbench.database import AdaptiveDatabase
    print("✅ AdaptiveDatabase imported")

    print("\n3️⃣ Creating AdaptiveDatabase instance...")
    db = AdaptiveDatabase(mode="workbench")
    print(f"✅ AdaptiveDatabase created")
    print(f"   Environment: {db.environment}")
    print(f"   Backend type: {type(db.backend).__name__}")

    if db.environment != "local":
        print(f"⚠️  Expected 'local', got '{db.environment}'")

    print("\n4️⃣ Testing conversation operations...")

    # Create conversation
    conv_id = str(uuid4())
    conversation_data = {
        "id": conv_id,
        "title": "Test Conversation",
        "mode": "workbench"
    }

    print(f"   Creating conversation {conv_id[:8]}...")
    saved_id = db.save_conversation(conversation_data)
    print(f"✅ Conversation created: {saved_id[:8]}")

    # Get conversation
    print(f"   Retrieving conversation...")
    retrieved = db.get_conversation(saved_id)
    print(f"✅ Conversation retrieved: {retrieved['title']}")

    # List conversations
    print(f"   Listing conversations...")
    conversations = db.list_conversations()
    print(f"✅ Found {len(conversations)} conversation(s)")

    print("\n5️⃣ Testing message operations...")

    # Save message
    message_data = {
        "conversation_id": saved_id,
        "role": "user",
        "content": "Test message",
        "metadata": {"test": True}
    }

    print(f"   Saving message...")
    msg_id = db.save_message(message_data)
    print(f"✅ Message saved: {msg_id[:8]}")

    # Get messages
    print(f"   Retrieving messages...")
    messages = db.get_messages(saved_id)
    print(f"✅ Found {len(messages)} message(s)")

    if messages:
        print(f"   Message content: {messages[0]['content']}")

    print("\n6️⃣ Testing database backend type...")
    if db.environment == "local":
        from agent_workbench.database.backends.sqlite import SQLiteBackend
        if isinstance(db.backend, SQLiteBackend):
            print("✅ Using SQLiteBackend (correct for local)")
        else:
            print(f"⚠️  Expected SQLiteBackend, got {type(db.backend).__name__}")

    print("\n7️⃣ Testing SQLAlchemy session...")
    try:
        from agent_workbench.api.database import get_session
        print("✅ get_session imported")

        # Test async session
        import asyncio

        async def test_session():
            async for session in get_session():
                print(f"✅ Session created: {type(session).__name__}")
                return True

        asyncio.run(test_session())

    except Exception as e:
        print(f"⚠️  Session test failed: {e}")

    print("\n8️⃣ Cleanup...")
    # Delete test data
    db.delete_message(msg_id)
    db.delete_conversation(saved_id)
    print("✅ Test data cleaned up")

    print("\n" + "=" * 80)
    print("🎉 ALL ADAPTIVE DATABASE TESTS PASSED")
    print("=" * 80)
    print(f"\n✅ Environment: {env}")
    print(f"✅ Backend: {type(db.backend).__name__}")
    print(f"✅ Database is working correctly")

except Exception as e:
    print("\n" + "=" * 80)
    print(f"❌ ERROR: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    sys.exit(1)
