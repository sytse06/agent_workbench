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

    # Sidebar visibility state - CLOSED by default (Phase 4.2)
    sidebar_visible = gr.State(value=False)

    # Note: visible=True so it's in DOM, but hidden via CSS display:none initially
    with gr.Sidebar(position="left", elem_id="conv-sidebar-container", visible=True):
        # New Chat button with icon (Phase 4.2: visible when sidebar open)
        new_chat_btn = gr.Button(
            "New Chat",
            icon="/static/icons/svg/add_chat_icon_24.svg",
            variant="primary",
            size="sm",
            elem_classes=["sidebar-new-chat-btn"],
        )

        gr.Markdown("## Recent Chats")

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

        # Action buttons at bottom
        with gr.Row():
            clear_storage_btn = gr.Button("🗑️ Clear History", size="sm", scale=1)

        # Collapse button removed - sidebar toggle in top bar now handles this

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
        None,  # collapse_btn removed - sidebar toggle in top bar now
        clear_storage_btn,
    )
