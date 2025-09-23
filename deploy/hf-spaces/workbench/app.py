#!/usr/bin/env python3
"""
HuggingFace Spaces entry point for Agent Workbench - Technical Mode
Generated deployment artifact that configures and launches the main application
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path for main application
current_dir = Path(__file__).parent
src_path = current_dir / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))
else:
    sys.path.insert(0, "src")

# Configure environment for workbench mode before importing main
os.environ.setdefault('APP_MODE', 'workbench')
os.environ.setdefault('ENABLE_PWA', 'true')
os.environ.setdefault('APP_TITLE', 'Agent Workbench - Technical')
os.environ.setdefault('APP_DESCRIPTION', 'AI development and research tool')
os.environ.setdefault('PWA_NAME', 'Agent Workbench')
os.environ.setdefault('PWA_SHORT_NAME', 'AgentWB-Tech')
os.environ.setdefault('PWA_THEME_COLOR', '#3b82f6')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./data/workbench.db')

# HF Spaces specific configuration
os.environ.setdefault('GRADIO_SERVER_NAME', '0.0.0.0')
os.environ.setdefault('GRADIO_SERVER_PORT', '7860')
os.environ.setdefault('GRADIO_SHARE', 'false')

# Import and run the main application
if __name__ == "__main__":
    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Import main application with HF Spaces configuration
    from agent_workbench.main import create_hf_spaces_app
    
    # Create and launch HF Spaces optimized app
    app = create_hf_spaces_app(mode='workbench')
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False,
        show_error=True,
        quiet=False
    )
