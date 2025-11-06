"""
Conversation history sidebar component.

Features:
- Dropdown-based conversation selection
- HTML list for visual display with JavaScript bridge
- Hybrid data source (API for auth users, BrowserState for guests)
- Feature-flagged via SHOW_CONV_BROWSER environment variable
"""

from typing import Any, Dict, Optional, Tuple

import gradio as gr


def get_sidebar_css() -> str:
    """
    Return CSS for conversation sidebar styling.

    Returns:
        CSS string with all sidebar styles
    """
    return """
    <style>
    .conv-list { padding: 10px 0; }
    .conv-item {
        padding: 12px;
        margin: 8px 0;
        cursor: pointer;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        transition: all 0.2s;
        background: white;
    }
    .conv-item:hover {
        background: #f5f5f5;
        border-color: #1976d2;
    }
    .conv-item.selected {
        background: #e3f2fd;
        border-color: #1976d2;
    }
    .conv-title {
        font-weight: 600;
        margin-bottom: 4px;
        color: #333;
    }
    .conv-meta {
        font-size: 0.85em;
        color: #666;
        margin-bottom: 4px;
    }
    .conv-preview {
        font-size: 0.9em;
        color: #888;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    #conv-dropdown {
        display: none !important;
    }
    </style>
    """


def render_sidebar(config: Dict[str, Any], user_state: gr.State) -> Tuple[
    Optional[gr.State],
    Optional[gr.HTML],
    Optional[gr.Button],
    Optional[gr.Button],
    Optional[gr.Dropdown],
    Optional[gr.Button],
]:
    """
    Render conversation history sidebar with list-based UI.

    Args:
        config: Mode configuration with feature flags
        user_state: User session state

    Returns:
        Tuple of (sidebar_visible, conv_list_html, new_chat_btn, collapse_btn,
                 conv_dropdown, clear_storage_btn)

    Feature Flag:
        SHOW_CONV_BROWSER: Whether to show conversation browser
        - Default: True for workbench, False for seo_coach
    """

    # Check if sidebar should be rendered
    if not config.get("show_conv_browser", False):
        return None, None, None, None, None, None

    # Sidebar visibility state
    sidebar_visible = gr.State(value=True)

    # Hidden dropdown for conversation selection (bridge for Gradio events)
    # JavaScript updates this dropdown when HTML list items are clicked
    # The dropdown's .change event triggers load_selected_conversation
    # NOTE: Must be visible=True for events to work,
    # hidden via CSS (#conv-dropdown rule)
    conv_dropdown = gr.Dropdown(
        label="Select conversation",
        choices=[],
        interactive=True,
        elem_id="conv-dropdown",
        visible=True,  # Must be visible for events to fire
    )

    with gr.Sidebar(position="left", elem_id="conv-sidebar-container"):
        gr.Markdown("## Recent Chats")

        # Action buttons
        with gr.Row():
            new_chat_btn = gr.Button(
                "➕ New Chat", variant="primary", size="sm", scale=2
            )
            clear_storage_btn = gr.Button("🗑️", size="sm", scale=1)

        # Collapse button
        collapse_btn = gr.Button("◀", variant="secondary", size="sm", scale=1)

        # Visible list rendered as HTML
        conv_list_html = gr.HTML(
            value="<div class='conv-list empty'>No conversations yet</div>",
            elem_id="conv-list-container",
        )

    # localStorage error handling and cleanup
    gr.HTML(
        """
        <script>
        (function() {
            // Check for corrupted localStorage and clear if needed
            try {
                const keys = [
                    'agent_workbench_conversation',
                    'agent_workbench_conversations_list'
                ];

                keys.forEach(key => {
                    try {
                        const data = localStorage.getItem(key);
                        if (data) {
                            // Try to parse to verify it's valid
                            JSON.parse(data);
                        }
                    } catch (e) {
                        console.warn(`[ConvSidebar] Corrupted data in ${key}:`, e);
                        console.log(`[ConvSidebar] Clearing ${key}`);
                        localStorage.removeItem(key);
                    }
                });
            } catch (e) {
                console.error('[ConvSidebar] localStorage check failed:', e);
            }
        })();
        </script>
        """
    )

    # JavaScript bridge for click-to-load conversation
    # Uses event delegation to handle clicks on conversation list items
    # Updates hidden dropdown and triggers Gradio's change event
    gr.HTML(
        """
        <script>
        (function() {
            console.log('[ConvSidebar] Initializing click bridge');

            // Wait for Gradio to render, then set up event delegation
            setTimeout(() => {
                const container = document.getElementById('conv-list-container');
                if (!container) {
                    console.error('[ConvSidebar] Container not found!');
                    return;
                }

                console.log('[ConvSidebar] Container found, setting up click handler');

                // Event delegation: listen on parent, handle clicks on .conv-item
                container.addEventListener('click', function(e) {
                    const item = e.target.closest('.conv-item');
                    if (!item) return;

                    const convId = item.dataset.id;
                    console.log('[ConvSidebar] Item clicked, ID:', convId);

                    // Find the hidden dropdown by ID
                    const dropdown = document.getElementById('conv-dropdown');
                    if (!dropdown) {
                        console.error(
                            '[ConvSidebar] Dropdown #conv-dropdown not found!'
                        );
                        return;
                    }

                    // Find the dropdown element (supports both old and new Gradio)
                    // Old Gradio: <select>
                    // New Gradio: <input role="listbox">
                    let dropdownElement = dropdown.querySelector('select');
                    if (!dropdownElement) {
                        dropdownElement = dropdown.querySelector(
                            'input[role="listbox"]'
                        );
                    }

                    if (!dropdownElement) {
                        console.error('[ConvSidebar] No dropdown element found!');
                        return;
                    }

                    console.log('[ConvSidebar] Setting dropdown value to:', convId);
                    dropdownElement.value = convId;

                    // Dispatch both input and change events for Gradio
                    dropdownElement.dispatchEvent(
                        new Event('input', {bubbles: true})
                    );
                    dropdownElement.dispatchEvent(
                        new Event('change', {bubbles: true})
                    );
                    console.log('[ConvSidebar] Events dispatched');

                    // Visual feedback: mark item as selected
                    document.querySelectorAll('.conv-item').forEach(i => {
                        i.classList.remove('selected');
                    });
                    item.classList.add('selected');
                });

                console.log('[ConvSidebar] Click bridge ready');
            }, 1000);  // Wait 1s for Gradio to fully render
        })();
        </script>
        """
    )

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
        conv_list_html,
        new_chat_btn,
        collapse_btn,
        conv_dropdown,
        clear_storage_btn,
    )
