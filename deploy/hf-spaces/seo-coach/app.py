#!/usr/bin/env python3
"""
HuggingFace Spaces entry point for Agent Workbench - SEO Coach Mode
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

# Configure environment for SEO coach mode before importing main
os.environ.setdefault('APP_MODE', 'seo_coach')
os.environ.setdefault('ENABLE_PWA', 'true')
os.environ.setdefault('APP_TITLE', 'SEO Coach - Nederland')
os.environ.setdefault('APP_DESCRIPTION',
                     'AI-powered SEO coaching voor Nederlandse bedrijven')
os.environ.setdefault('PWA_NAME', 'SEO Coach')
os.environ.setdefault('PWA_SHORT_NAME', 'SEO-Coach')
os.environ.setdefault('PWA_THEME_COLOR', '#10b981')
os.environ.setdefault('DEFAULT_LANGUAGE', 'nl')

# HuggingFace Spaces - Use Hub DB for persistence
os.environ.setdefault('USE_HUB_DB', 'true')
os.environ.setdefault('HUB_DB_REPO', 'sytse06/agent-seo-coach-db')
# Fallback DATABASE_URL for compatibility
os.environ.setdefault('DATABASE_URL',
                     'sqlite+aiosqlite:///./data/seo_coach.db')

# HF Spaces specific configuration
os.environ.setdefault('GRADIO_SERVER_NAME', '0.0.0.0')
os.environ.setdefault('GRADIO_SERVER_PORT', '7860')
os.environ.setdefault('GRADIO_SHARE', 'false')

# LiteLLM configuration for OpenRouter API integration
os.environ.setdefault('USE_LITELLM', 'true')
os.environ.setdefault('DEFAULT_MODEL', 'openai/gpt-3.5-turbo')
# Note: Set OPENROUTER_API_KEY in HF Spaces environment variables
# This gives access to 100+ models via single API key

# Import and run the main application
if __name__ == "__main__":
    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Import main application with HF Spaces configuration
    from agent_workbench.main import create_hf_spaces_app
    
    # Create and launch HF Spaces optimized app
    app = create_hf_spaces_app(mode='seo_coach')
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False,
        show_error=True,
        quiet=False
    )
