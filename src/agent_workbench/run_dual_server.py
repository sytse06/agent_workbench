#!/usr/bin/env python
"""Run FastAPI and Gradio as separate processes - the working approach."""

import os
import sys
import threading

import uvicorn
from dotenv import load_dotenv

# Load environment
load_dotenv(".env", override=True)
app_env = os.getenv("APP_ENV", "development")
env_file = f"config/{app_env}.env"
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"✅ Loaded {app_env} environment from {env_file}")

os.environ.setdefault("APP_MODE", "workbench")

print("=" * 80)
print("🚀 Starting Agent Workbench - Dual Server Mode")
print("=" * 80)
print("   FastAPI:  http://localhost:8000/docs")
print("   Gradio UI: http://localhost:7860")
print("=" * 80)


def run_gradio():
    """Run Gradio interface on port 7860."""
    print("\n🎨 Starting Gradio UI server...")
    from agent_workbench.ui.mode_factory import ModeFactory

    mode = os.getenv("APP_MODE", "workbench")
    factory = ModeFactory()
    interface = factory.create_interface(mode=mode)

    print(f"✅ Created {mode} interface")
    print("🚀 Launching Gradio on http://localhost:7860")

    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False,
    )


def run_fastapi():
    """Run FastAPI server on port 8000."""
    print("\n🔧 Starting FastAPI server...")

    # Import the app WITHOUT Gradio mounting
    os.environ["SKIP_GRADIO_MOUNT"] = "true"
    from agent_workbench.main import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    # Start Gradio in a separate thread
    gradio_thread = threading.Thread(target=run_gradio, daemon=True)
    gradio_thread.start()

    print("\n⏳ Waiting for Gradio to initialize...")
    import time

    time.sleep(2)

    # Start FastAPI in main thread
    try:
        run_fastapi()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
