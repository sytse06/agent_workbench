#!/usr/bin/env python
"""Test Gradio standalone to verify it's not a Gradio issue."""

import os
os.environ["APP_MODE"] = "workbench"
os.environ["APP_ENV"] = "development"

print("🎯 Testing Gradio standalone...")

from agent_workbench.ui.mode_factory import ModeFactory

# Create interface
factory = ModeFactory()
interface = factory.create_interface(mode="workbench")

print("✅ Interface created")
print("🚀 Launching on http://localhost:7860")
print("   Press Ctrl+C to stop")
print("   Note: Not using queue() for better compatibility")

# Launch standalone (without queue for testing)
interface.launch(
    server_name="127.0.0.1",
    server_port=7860,
    share=False,
    show_error=True
)
