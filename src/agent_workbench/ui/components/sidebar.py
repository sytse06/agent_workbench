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
    Optional[gr.Column],
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
        Tuple of (sidebar_visible, sidebar_col, conv_list, new_chat_btn,
                 collapse_btn, clear_storage_btn)

    Feature Flag:
        SHOW_CONV_BROWSER: Whether to show conversation browser
        - Default: True for workbench, False for seo_coach
    """

    # Check if sidebar should be rendered
    if not config.get("show_conv_browser", False):
        return None, None, None, None, None, None

    # Sidebar visibility state - CLOSED by default (Phase 4.2)
    sidebar_visible = gr.State(value=False)

    # Using gr.Column for sidebar to enable push behavior (not overlay)
    # Designer's recommendation: scale=1, min_width=250
    # visible=True so it's in DOM, starts HIDDEN via
    # conv-sidebar-hidden class (width: 0)
    with gr.Column(
        scale=1,
        min_width=250,
        elem_id="conv-sidebar-container",
        visible=True,
        elem_classes=["agent-workbench-sidebar", "conv-sidebar-hidden"],  # Start hidden
    ) as sidebar_col:
        # New Chat button with icon
        # New Chat button - Visual HTML + Hidden Logic Button pattern
        # Matches chat container icon pattern using sprite.svg
        gr.HTML(
            value=(
                '<div class="sidebar-new-chat-visual" '
                "onclick=\"document.querySelector('.sidebar-new-chat-btn').click()\">"
                '<svg class="icon">'
                '<use href="/static/icons/sprite.svg#new-chat"/>'
                "</svg>"
                "<span>New Chat</span>"
                "</div>"
            )
        )

        # Hidden button that actually triggers the event
        # Must be visible=True so it's in DOM, but hidden with CSS
        new_chat_btn = gr.Button(
            "New Chat",
            visible=True,
            elem_classes=["sidebar-new-chat-btn"],  # Targeted by JS onclick and top bar
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
        sidebar_col,  # Return column reference for visibility toggling
        conv_list,
        new_chat_btn,
        None,  # collapse_btn removed - sidebar toggle in top bar now
        clear_storage_btn,
    )
