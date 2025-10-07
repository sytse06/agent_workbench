#!/usr/bin/env python
"""Test script to verify standardized Gradio UI pattern works."""

import os
import sys

# Set environment before importing
os.environ["APP_MODE"] = "workbench"
os.environ["APP_ENV"] = "development"

print("=" * 80)
print("🧪 Testing Standardized Gradio UI Pattern")
print("=" * 80)

def test_mode_factory():
    """Test 1: ModeFactory creates interface correctly."""
    print("\n1️⃣ Testing ModeFactory...")
    from agent_workbench.ui.mode_factory import ModeFactory

    factory = ModeFactory()
    interface = factory.create_interface(mode="workbench")

    assert interface is not None, "Interface should not be None"
    print("✅ ModeFactory creates interface")

    return interface


def test_create_function():
    """Test 2: create_fastapi_mounted_gradio_interface works."""
    print("\n2️⃣ Testing create_fastapi_mounted_gradio_interface...")
    from agent_workbench.main import create_fastapi_mounted_gradio_interface

    interface = create_fastapi_mounted_gradio_interface()

    assert interface is not None, "Interface should not be None"
    print("✅ create_fastapi_mounted_gradio_interface works")

    return interface


def test_queue():
    """Test 3: Queue can be applied."""
    print("\n3️⃣ Testing queue application...")
    from agent_workbench.ui.mode_factory import ModeFactory

    factory = ModeFactory()
    interface = factory.create_interface(mode="workbench")

    try:
        interface.queue()
        print("✅ Queue applied successfully")
        return True
    except Exception as e:
        print(f"⚠️  Queue application failed: {e}")
        return False


def test_fastapi_mounting():
    """Test 4: Interface can be mounted in FastAPI."""
    print("\n4️⃣ Testing FastAPI mounting...")
    import gradio as gr
    from fastapi import FastAPI
    from agent_workbench.main import create_fastapi_mounted_gradio_interface

    # Create clean FastAPI app
    test_app = FastAPI()

    # Create interface
    interface = create_fastapi_mounted_gradio_interface()
    interface.queue()

    # Mount
    try:
        test_app = gr.mount_gradio_app(test_app, interface, path="/")
        print("✅ Interface mounted in FastAPI at /")
        return True
    except Exception as e:
        print(f"❌ Mounting failed: {e}")
        return False


def test_mode_switching():
    """Test 5: Mode switching works."""
    print("\n5️⃣ Testing mode switching...")
    from agent_workbench.ui.mode_factory import ModeFactory

    factory = ModeFactory()

    # Test workbench mode
    os.environ["APP_MODE"] = "workbench"
    workbench_ui = factory.create_interface(mode="workbench")
    assert workbench_ui is not None
    print("✅ Workbench mode works")

    # Test seo_coach mode
    os.environ["APP_MODE"] = "seo_coach"
    seo_ui = factory.create_interface(mode="seo_coach")
    assert seo_ui is not None
    print("✅ SEO Coach mode works")

    return True


def test_full_app_import():
    """Test 6: Full app can be imported."""
    print("\n6️⃣ Testing full app import...")
    try:
        from agent_workbench.main import app
        assert app is not None
        print("✅ Full app imports successfully")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n📋 Running standardization tests...\n")

    results = []

    try:
        results.append(("ModeFactory", test_mode_factory() is not None))
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        results.append(("ModeFactory", False))

    try:
        results.append(("create_function", test_create_function() is not None))
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        results.append(("create_function", False))

    try:
        results.append(("queue", test_queue()))
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        results.append(("queue", False))

    try:
        results.append(("fastapi_mounting", test_fastapi_mounting()))
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        results.append(("fastapi_mounting", False))

    try:
        results.append(("mode_switching", test_mode_switching()))
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        results.append(("mode_switching", False))

    try:
        results.append(("full_app_import", test_full_app_import()))
    except Exception as e:
        print(f"❌ Test 6 failed: {e}")
        results.append(("full_app_import", False))

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Results Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 80)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("=" * 80)
        print("\n✅ Standardized Gradio pattern is working correctly!")
        print("   You can now run: make start-app")
        sys.exit(0)
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 80)
        print("\n❌ Some issues need to be fixed before standardization is complete")
        sys.exit(1)
