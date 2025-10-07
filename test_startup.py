#!/usr/bin/env python
"""Test script to debug Gradio startup issues."""

import os
import sys

# Set environment before importing
os.environ["APP_MODE"] = "workbench"
os.environ["APP_ENV"] = "development"

print("=" * 80)
print("🔍 TESTING GRADIO STARTUP")
print("=" * 80)

try:
    print("\n1️⃣ Testing ModeFactory import...")
    from agent_workbench.ui.mode_factory import ModeFactory
    print("✅ ModeFactory imported")

    print("\n2️⃣ Creating ModeFactory instance...")
    factory = ModeFactory()
    print("✅ ModeFactory instance created")

    print("\n3️⃣ Creating interface...")
    interface = factory.create_interface(mode="workbench")
    print(f"✅ Interface created: {type(interface)}")

    print("\n4️⃣ Applying queue...")
    interface.queue()
    print("✅ Queue applied")

    print("\n5️⃣ Testing main.py import...")
    from agent_workbench import main
    print("✅ main.py imported")

    print("\n6️⃣ Testing create_fastapi_mounted_gradio_interface...")
    test_interface = main.create_fastapi_mounted_gradio_interface()
    print(f"✅ Interface from main: {type(test_interface)}")

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED")
    print("=" * 80)

except Exception as e:
    print("\n" + "=" * 80)
    print(f"❌ ERROR: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    sys.exit(1)
