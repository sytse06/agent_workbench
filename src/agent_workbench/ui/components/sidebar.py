"""
Conversation history sidebar component.

Features:
- Collapsible sidebar with conversation list
- Card-based UI (title, timestamp, preview)
- Click to load conversation
- Feature-flagged via SHOW_CONV_BROWSER environment variable
- Hybrid toggle approach (state + CSS + click-away)
- Full accessibility (ARIA attributes)
"""

from typing import Any, Dict

import gradio as gr


def render_sidebar(
    config: Dict[str, Any], user_state: gr.State
) -> tuple[gr.State, gr.HTML, gr.Button, gr.Button]:
    """
    Render conversation history sidebar.

    Args:
        config: Mode configuration with feature flags
        user_state: User session state

    Returns:
        Tuple of (sidebar_visible_state, conv_list_html, new_chat_btn,
        collapse_btn)

    Feature Flag:
        SHOW_CONV_BROWSER: Whether to show conversation browser
        - Default: True for workbench, False for seo_coach
    """

    # Check if sidebar should be rendered
    if not config.get("show_conv_browser", False):
        return None, None, None, None

    # Sidebar visibility state (source of truth)
    sidebar_visible = gr.State(True)

    with gr.Sidebar(position="left", elem_id="conv-sidebar-container"):
        gr.Markdown("## Recent Chats")

        # Conversation list container (populated by JavaScript)
        conv_list_html = gr.HTML(
            elem_id="conv-sidebar",
            label="Conversations",
            visible=True,
        )

        # New chat button
        new_chat_btn = gr.Button("➕ New Chat", variant="primary", size="sm", scale=1)

        # Collapse button
        collapse_btn = gr.Button(
            "Hide sidebar", variant="secondary", size="sm", scale=1
        )

    return sidebar_visible, conv_list_html, new_chat_btn, collapse_btn


def create_sidebar_javascript() -> str:
    """
    Create JavaScript for sidebar functionality.

    Includes:
    - Fetch conversation list from API
    - Render conversation cards
    - Click handlers for loading conversations
    - Click-away listener
    - ARIA attributes
    """

    return """
    <script>
    (async () => {
        // Fetch conversation list on page load
        try {
            const res = await fetch('/api/v1/conversations', {
                credentials: 'include'  // Include auth cookies
            });

            if (!res.ok) {
                console.error('Failed to fetch conversations:', res.status);
                document.getElementById('conv-sidebar').innerHTML =
                    '<p style="color: #666; padding: 16px;">Error loading ' +
                    'conversations</p>';
                return;
            }

            const convs = await res.json();
            const container = document.getElementById('conv-sidebar');

            // Empty state
            if (!convs || convs.length === 0) {
                container.innerHTML =
                    '<p style="color: #999; padding: 16px; ' +
                    'text-align: center;">No conversations yet</p>';
                return;
            }

            // Render conversation cards
            container.innerHTML = convs.map(c => `
                <div class="conv-card" data-id="${c.id}" role="button" tabindex="0"
                     aria-label="Load conversation: ${c.title || 'Untitled'}">
                    <div class="conv-card-header">
                        <strong>${c.title || 'Untitled'}</strong>
                    </div>
                    <div class="conv-card-meta">
                        <small>${new Date(c.updated_at).toLocaleString()}</small>
                    </div>
                    <div class="conv-card-preview">
                        ${(c.preview || '').substring(0, 100)}...
                    </div>
                </div>
            `).join('');

            // Add click handlers to cards
            document.querySelectorAll('.conv-card').forEach(el => {
                const clickHandler = async () => {
                    const convId = el.dataset.id;
                    console.log('Loading conversation:', convId);

                    try {
                        // Fetch full conversation details
                        const res = await fetch(`/api/v1/conversations/${convId}`, {
                            credentials: 'include'
                        });

                        if (!res.ok) {
                            console.error('Failed to fetch conversation');
                            return;
                        }

                        const conv = await res.json();

                        // Dispatch custom event for Gradio integration
                        window.dispatchEvent(new CustomEvent('load-conversation', {
                            detail: {
                                conversationId: convId,
                                title: conv.title,
                                messages: conv.messages
                            }
                        }));
                    } catch (err) {
                        console.error('Error loading conversation:', err);
                    }
                };

                // Click event
                el.addEventListener('click', clickHandler);

                // Keyboard event (Enter key)
                el.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        clickHandler();
                    }
                });
            });

        } catch (err) {
            console.error('Error in sidebar setup:', err);
        }
    })();

    // Global click-away listener (collapse sidebar on outside click)
    (function() {
        const sidebar = document.querySelector('.gr-sidebar');
        if (!sidebar) return;

        document.addEventListener('click', function(e) {
            // Don't collapse if clicking inside sidebar
            if (sidebar.contains(e.target)) return;

            // Don't collapse if clicking the app root
            if (e.target === document.querySelector('.gradio-app')) return;

            // Collapse sidebar
            sidebar.classList.add('gr-sidebar-collapsed');
            sidebar.setAttribute('aria-hidden', 'true');
            console.log('Sidebar collapsed by click-away');
        });
    })();

    // Set initial ARIA attributes
    (function() {
        const sidebar = document.querySelector('.gr-sidebar');
        if (sidebar) {
            sidebar.setAttribute('aria-label', 'Conversation history sidebar');
            sidebar.setAttribute('aria-hidden', 'false');
        }
    })();
    </script>
    """


def create_sidebar_css() -> str:
    """
    Create CSS for sidebar styling and animations.

    Includes:
    - Sidebar collapse animation
    - Conversation card styling
    - Hover states
    - Responsive design
    """

    return """
    <style>
    /* Sidebar container */
    .gr-sidebar {
        transition: width 0.3s ease, opacity 0.3s ease;
        opacity: 1;
        width: auto;
    }

    .gr-sidebar.gr-sidebar-collapsed {
        width: 0 !important;
        overflow: hidden;
        opacity: 0;
        transition: width 0.3s ease, opacity 0.3s ease;
    }

    /* Conversation cards */
    #conv-sidebar .conv-card {
        border: 1px solid var(--border-color-primary, #e0e0e0);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
        background: var(--background-fill-primary, #fff);
        outline: none;
    }

    #conv-sidebar .conv-card:hover,
    #conv-sidebar .conv-card:focus {
        background: var(--background-fill-secondary, #f5f5f5);
        border-color: var(--color-accent, #3b82f6);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    #conv-sidebar .conv-card-header {
        font-size: 14px;
        font-weight: 600;
        color: var(--body-text-color, #000);
        margin-bottom: 4px;
    }

    #conv-sidebar .conv-card-meta {
        font-size: 11px;
        color: var(--body-text-color-subdued, #666);
        margin-bottom: 4px;
    }

    #conv-sidebar .conv-card-preview {
        font-size: 12px;
        color: var(--body-text-color-subdued, #666);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-style: italic;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .gr-sidebar {
            max-width: 200px;
        }

        .gr-sidebar.gr-sidebar-collapsed {
            max-width: 0;
        }
    }
    </style>
    """
