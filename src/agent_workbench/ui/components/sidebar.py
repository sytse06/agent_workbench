"""
Conversation history sidebar component.

Features:
- Native Gradio Dataset list for conversation selection
- Hybrid data source (API for auth users, BrowserState for guests)
- Feature-flagged via SHOW_CONV_BROWSER environment variable
"""

from typing import Any, Dict, Optional, Tuple

import gradio as gr


def render_sidebar(config: Dict[str, Any], user_state: gr.State) -> Tuple[
    Optional[gr.State],
    Optional[gr.Dataset],
    Optional[gr.Button],
    Optional[gr.Button],
    Optional[gr.Button],
]:
    """
    Render conversation history sidebar with native Gradio Dataset list.

    Args:
        config: Mode configuration with feature flags
        user_state: User session state

    Returns:
        Tuple of (sidebar_visible, conv_list, new_chat_btn,
                 collapse_btn, clear_storage_btn)

    Feature Flag:
        SHOW_CONV_BROWSER: Whether to show conversation browser
        - Default: True for workbench, False for seo_coach
    """

    # Check if sidebar should be rendered
    if not config.get("show_conv_browser", False):
        return None, None, None, None, None

    # Sidebar visibility state
    sidebar_visible = gr.State(value=True)

    with gr.Sidebar(position="left", elem_id="conv-sidebar-container"):
        gr.Markdown("## Recent Chats")

        # Action buttons
        with gr.Row():
            new_chat_btn = gr.Button(
                "➕ New Chat", variant="primary", size="sm", scale=2
            )
            clear_storage_btn = gr.Button("🗑️", size="sm", scale=1)

        # Native Gradio Dataset list for conversation selection
        conv_list = gr.Dataset(
            components=[gr.Textbox(visible=False)],
            samples=[],
            label="Recent Chats",
            show_label=False,
            layout="table",
            type="index",
            elem_id="conv-list",
            samples_per_page=20,
        )

        # Collapse button
        collapse_btn = gr.Button("◀", variant="secondary", size="sm", scale=1)

    # Clear storage button - clears localStorage
    clear_storage_btn.click(
        fn=None,
        js="""
        () => {
            localStorage.removeItem('agent_workbench_conversation');
            localStorage.removeItem('agent_workbench_conversations_list');
            console.log('[ConvSidebar] localStorage cleared');
            return null;
        }
        """,
    )

    return (
        sidebar_visible,
        conv_list,
        new_chat_btn,
        collapse_btn,
        clear_storage_btn,
    )
