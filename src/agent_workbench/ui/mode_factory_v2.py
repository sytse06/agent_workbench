"""
Mode Factory V2 - Creates Gradio app based on APP_MODE environment variable.

Pattern:
    create_app() → create_workbench_app() OR create_seo_app()
                → build_gradio_app(config)

No code duplication - single builder, different configurations.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import gradio as gr

from .pages import chat, settings

logger = logging.getLogger(__name__)


def create_app() -> gr.Blocks:
    """
    Entry point - creates Gradio app based on APP_MODE environment variable.

    Returns:
        gr.Blocks: Single Gradio Blocks instance with routes
    """
    mode = os.getenv("APP_MODE", "workbench")

    if mode == "workbench":
        return create_workbench_app()
    elif mode == "seo_coach":
        return create_seo_app()
    else:
        # Fallback to workbench
        return create_workbench_app()


def create_workbench_app() -> gr.Blocks:
    """
    Workbench mode configuration - technical users.

    Returns:
        gr.Blocks: Configured Gradio app for workbench mode
    """
    config = {
        "title": "Agent Workbench",
        "theme": gr.themes.Base(primary_hue="blue", font="Roboto"),  # Blue theme
        # English labels
        "labels": {
            # Chat page
            "placeholder": "Type your message...",
            "send": "Send",
            # Settings page
            "models_tab": "🤖 Models",
            "appearance_tab": "🎨 Appearance",
            "context_tab": "📁 Project Info",
            "account_tab": "👤 Account",
            # Model settings
            "provider_label": "Provider",
            "model_label": "Model",
            "temperature_label": "Temperature",
            "max_tokens_label": "Max Tokens",
            # Context fields
            "context_name": "Project Name",
            "context_url": "Project URL",
            "context_description": "Description",
            # Locked model message (not shown in workbench)
            "model_locked": "Current Model",
            "model_locked_info": "Model selection available in this mode",
        },
        # Feature flags
        "allow_model_selection": True,  # Show model controls in settings
        "show_company_section": False,  # Hide business-specific fields
        "show_conv_browser": os.getenv("SHOW_CONV_BROWSER", "true").lower()
        == "true",  # Show conversation sidebar
        # Default model config
        "available_providers": ["openrouter", "google"],
        "default_provider": "openrouter",
        "available_models": [
            "gpt-5-mini",
            "qwen3-30b-a3b",
            "gemini-2.5-flash",
            "gemini-2.0-flash-lite",
        ],
        "default_model": "gpt-4-turbo",
    }

    return build_gradio_app(config)


def create_seo_app() -> gr.Blocks:
    """
    SEO coach mode configuration - business users.

    Returns:
        gr.Blocks: Configured Gradio app for SEO coach mode
    """
    config = {
        "title": "SEO Coach",
        "theme": gr.themes.Base(primary_hue="green", font="Open Sans"),  # Green theme
        # Dutch labels
        "labels": {
            # Chat page
            "placeholder": "Stel je vraag over SEO...",
            "send": "Verstuur",
            # Settings page
            "models_tab": "🤖 AI Model",
            "appearance_tab": "🎨 Weergave",
            "context_tab": "🏢 Bedrijfsinfo",
            "account_tab": "👤 Account",
            # Model settings
            "provider_label": "AI Provider",
            "model_label": "Model",
            "temperature_label": "Creativiteit",
            "max_tokens_label": "Max Tokens",
            # Context fields (business-oriented)
            "context_name": "Bedrijfsnaam",
            "context_url": "Website URL",
            "context_description": "Beschrijving",
            "business_type": "Type bedrijf",
            "location": "Locatie",
            # Locked model message
            "model_locked": "Huidig model",
            "model_locked_info": "SEO Coach gebruikt het beste model voor jou",
        },
        # Feature flags
        "allow_model_selection": False,  # Lock model in settings
        "show_company_section": True,  # Show business fields
        "show_conv_browser": os.getenv("SHOW_CONV_BROWSER", "false").lower()
        == "true",  # Hide conversation sidebar in SEO coach
        # Default model config (locked to best model)
        "available_providers": ["openrouter"],
        "default_provider": "openrouter",
        "available_models": ["qwen3-30b-a3b"],
        "default_model": "qwen3-30b-a3b",
    }

    return build_gradio_app(config)


def build_gradio_app(config: Dict[str, Any]) -> gr.Blocks:
    """
    Single Gradio app builder - shared by all modes.

    This function is called by create_workbench_app() and create_seo_app()
    with different configurations. It builds the SAME component tree for
    both modes - differences are controlled by config values.

    Args:
        config: Mode configuration dictionary

    Returns:
        gr.Blocks: Configured Gradio app with routes

    Critical Pattern:
        - ALL components must be defined (use visible= to hide)
        - Shared state defined at demo level, passed to render functions
        - Single queue() call happens in main.py, not here

    Phase 2: Now includes settings_state for sharing config between pages
    """

    # Create Blocks instance with unified CSS
    # main.css imports fonts.css + shared.css (all core styles)
    # Critical CSS inlined to bypass browser caching issues

    # Tell Gradio to serve the static directory as static files
    # This allows gr.Button(icon="...") to serve icons without permission checks
    # Ref: https://www.gradio.app/docs/gradio/set_static_paths
    static_dir = Path(__file__).resolve().parent.parent / "static"
    gr.set_static_paths(paths=[str(static_dir)])

    # Load custom CSS directly - @import doesn't work in Gradio's inline styles
    # Must load tokens.css first for CSS variables, then styles.css
    css_dir = static_dir / "assets" / "css"
    tokens_css = (
        (css_dir / "tokens.css").read_text()
        if (css_dir / "tokens.css").exists()
        else ""
    )
    styles_css = (
        (css_dir / "styles.css").read_text()
        if (css_dir / "styles.css").exists()
        else ""
    )

    # Remove @import statements from styles.css since we're loading tokens.css separately
    styles_css = "\n".join(
        line
        for line in styles_css.split("\n")
        if not line.strip().startswith("@import")
    )

    demo = gr.Blocks(
        title=config["title"],
        theme=config["theme"],
        css=f"""
        /* Google Fonts loaded via FastAPI middleware (main.py:inject_google_fonts)
           Gradio's Constructable Stylesheets don't support @import for external URLs */

        /* Design tokens (CSS variables) */
        {tokens_css}

        /* Custom component styles */
        {styles_css}

        /* Critical fix: prevent input bar wrapping (Phase 4.3) */
        .agent-workbench-input-bar {{
            flex-wrap: nowrap !important;
        }}
        """,
    )

    # Define shared state BEFORE routes so all routes can access them
    with demo:
        user_state = gr.State(None)  # User session/auth data
        conversation_state = gr.State([])  # Current conversation messages

        # Settings state - persisted via gr.BrowserState for guest users
        # Database persistence remains primary for authenticated users
        settings_state = gr.State({})  # Session state (resets on page refresh)

    # Route 1: Chat page (default, shown at root "/" path)
    with demo:
        # Capture BrowserState and Dataset list returned from chat page
        conversations_list_storage, conv_list = chat.render(
            config, user_state, conversation_state, settings_state
        )

        # DEBUG: Check what chat.render() returned
        print("[DEBUG mode_factory_v2] After chat.render():")
        print(f"  conversations_list_storage: {conversations_list_storage}")
        print(f"  conv_list: {conv_list}")
        print(f"  Type conversations_list_storage: {type(conversations_list_storage)}")
        print(f"  Type conv_list: {type(conv_list)}")

        # Auto-load conversation history into Dataset list from BrowserState
        # on page load (only for guest users - auth users use database)
        if conversations_list_storage and conv_list:
            print("[DEBUG mode_factory_v2] IF condition passed - setting up load event")

            @demo.load(
                inputs=[user_state, conversations_list_storage], outputs=[conv_list]
            )
            def load_conversations_from_browser(user_state_val, stored_conversations):
                """
                Load conversation history from BrowserState (localStorage).

                For guest users only - authenticated users use database.
                """
                print("[DEBUG mode_factory_v2] load_conversations_from_browser CALLED!")
                print(f"  user_state_val: {user_state_val}")
                print(
                    f"  stored_conversations length: {len(stored_conversations or [])}"
                )

                from .pages.chat import populate_list

                result = populate_list(user_state_val, stored_conversations or [])
                print(f"[DEBUG mode_factory_v2] populate_list returned: {result}")
                return result

        else:
            print(
                "[DEBUG mode_factory_v2] IF condition FAILED - " "load event NOT set up"
            )
            storage_is_none = conversations_list_storage is None
            print(f"  conversations_list_storage is None: {storage_is_none}")
            print(f"  conv_list is None: {conv_list is None}")

        # Phase 4.2: Logo/chatbot visibility toggle + icon bar functionality
        # Toggle visibility based on message count (Ollama design pattern)
        # Handle sidebar toggle, new chat, and settings icon clicks
        demo.load(
            fn=None,
            js="""
            function() {
                // Wait for Gradio to fully render
                setTimeout(() => {
                    const chatbot = document.querySelector('.agent-workbench-messages');
                    const logo = document.querySelector('.agent-workbench-logo');

                    if (!chatbot || !logo) return;

                    // Check if chatbot has real messages
                    const msgSelectors = [
                        '[data-testid*="message"]',
                        '.message',
                        '[role="user"]',
                        '[role="assistant"]'
                    ].join(', ');
                    const messageElements = chatbot.querySelectorAll(
                        msgSelectors
                    );
                    const hasMessages = messageElements.length > 0;
                    const textContent = chatbot.textContent.trim();
                    const hasRealContent = (
                        textContent.length > 10 &&
                        textContent !== 'Chatbot'
                    );

                    if (hasMessages || hasRealContent) {
                        // Has messages: Hide logo, show chatbot
                        logo.style.display = 'none';
                        chatbot.style.display = 'block';
                    } else {
                        // No messages: Show logo, hide chatbot
                        logo.style.display = 'flex';
                        chatbot.style.display = 'none';
                    }

                    // Watch for changes to chatbot (new messages)
                    const observer = new MutationObserver(() => {
                        const msgs = chatbot.querySelectorAll(
                            msgSelectors
                        );
                        const hasNewMessages = msgs.length > 0;

                        if (hasNewMessages) {
                            logo.style.display = 'none';
                            chatbot.style.display = 'block';
                        } else {
                            logo.style.display = 'flex';
                            chatbot.style.display = 'none';
                        }
                    });

                    observer.observe(chatbot, {
                        childList: true,
                        subtree: true,
                        characterData: true
                    });

                    // Phase 4.2: Icon bar functionality
                    // Sidebar toggle button - using gr.Column with native visibility
                    const sidebarToggleBtn = document.getElementById(
                        'sidebar-toggle-btn'
                    );
                    const sidebarCol = document.getElementById(
                        'conv-sidebar-container'
                    );
                    const topBarNewChatBtn = document.getElementById(
                        'new-chat-container'
                    );
                    let sidebarOpen = false;

                    console.log('[Sidebar] Toggle button:', sidebarToggleBtn);
                    console.log('[Sidebar] Column element:', sidebarCol);
                    console.log('[Sidebar] New chat button:', topBarNewChatBtn);
                    console.log('[Sidebar] New chat button classes:', topBarNewChatBtn?.className);

                    // Debug: Check initial sidebar state
                    console.log('[Sidebar] Initial sidebar classes:', sidebarCol?.className);
                    console.log('[Sidebar] Has conv-sidebar-hidden class:', sidebarCol?.classList.contains('conv-sidebar-hidden'));

                    // Initialize: Ensure new chat icon is visible when sidebar is closed
                    if (topBarNewChatBtn) {
                        topBarNewChatBtn.classList.remove('hidden-when-sidebar-open');
                        console.log('[Sidebar] Initial state: new chat icon visible, classes:', topBarNewChatBtn.className);
                    }

                    // Create backdrop element for mobile (click to close)
                    let backdrop = null;

                    function closeSidebar() {
                        sidebarOpen = false;
                        sidebarCol.classList.add('conv-sidebar-hidden');
                        console.log('[Sidebar] Hiding sidebar');

                        // Show top bar new chat button
                        if (topBarNewChatBtn) {
                            topBarNewChatBtn.classList.remove('hidden-when-sidebar-open');
                            console.log('[Sidebar] Showing top bar new chat icon');
                        }

                        // Remove backdrop
                        if (backdrop) {
                            backdrop.remove();
                            backdrop = null;
                            console.log('[Sidebar] Removed backdrop');
                        }
                    }

                    function openSidebar() {
                        sidebarOpen = true;
                        sidebarCol.classList.remove('conv-sidebar-hidden');
                        console.log('[Sidebar] Showing sidebar');

                        // Hide top bar new chat button
                        if (topBarNewChatBtn) {
                            topBarNewChatBtn.classList.add('hidden-when-sidebar-open');
                            console.log('[Sidebar] Hiding top bar new chat icon');
                        }

                        // Create backdrop (mobile only - click to close)
                        if (window.innerWidth <= 768) {
                            backdrop = document.createElement('div');
                            backdrop.id = 'sidebar-backdrop';
                            backdrop.style.cssText = `
                                position: fixed;
                                top: 0;
                                left: 0;
                                width: 100vw;
                                height: 100vh;
                                background: rgba(0, 0, 0, 0.5);
                                z-index: 1999;
                                cursor: pointer;
                            `;
                            backdrop.addEventListener('click', closeSidebar);
                            document.body.appendChild(backdrop);
                            console.log('[Sidebar] Created backdrop (mobile)');
                        }
                    }

                    if (sidebarToggleBtn && sidebarCol) {
                        console.log('[Sidebar] Wiring up click handler');
                        sidebarToggleBtn.addEventListener('click', () => {
                            console.log('[Sidebar] ====== Toggle clicked, open:', sidebarOpen, '======');

                            if (sidebarOpen) {
                                closeSidebar();
                            } else {
                                openSidebar();
                            }
                        });
                    } else {
                        console.warn('[Sidebar] Could not find elements - toggle button or sidebar column missing');
                        console.warn('[Sidebar] sidebarToggleBtn:', sidebarToggleBtn);
                        console.warn('[Sidebar] sidebarCol:', sidebarCol);
                    }

                    // Settings icon click
                    const settingsIcon = document.getElementById('settings-icon');
                    if (settingsIcon) {
                        settingsIcon.addEventListener('click', () => {
                            window.location.href = '/settings';
                        });
                    }

                    // Top bar new chat button click (when sidebar closed)
                    const newChatBtn = document.getElementById(
                        'new-chat-btn'
                    );
                    if (newChatBtn) {
                        newChatBtn.addEventListener('click', () => {
                            // Trigger sidebar new chat button
                            const sidebarNewChatBtn = (
                                document.querySelector(
                                    '.sidebar-new-chat-btn'
                                )
                            );
                            if (sidebarNewChatBtn) {
                                sidebarNewChatBtn.click();
                            }
                        });
                    }

                    // MOBILE FIX: Remove main element padding on mobile to allow full-width top bar
                    if (window.innerWidth <= 768) {
                        const main = document.querySelector('main.fillable');
                        if (main) {
                            main.style.paddingLeft = '0';
                            main.style.paddingRight = '0';
                            console.log('[Mobile] Removed main padding for full-width layout');
                        }

                        // MOBILE FIX: Remove padding/margin from component-16 to eliminate left offset
                        const component16 = document.querySelector('#component-16');
                        if (component16) {
                            component16.style.paddingLeft = '0';
                            component16.style.paddingRight = '0';
                            component16.style.marginLeft = '0';
                            component16.style.marginRight = '0';
                            console.log('[Mobile] Removed component-16 padding/margin');
                        }

                        // MOBILE FIX: Position top bar at left edge
                        const topBar = document.querySelector('#component-17');
                        if (topBar) {
                            topBar.style.marginLeft = '0';
                            topBar.style.marginRight = '0';
                            topBar.style.position = 'relative';
                            topBar.style.left = '0';
                            console.log('[Mobile] Positioned top bar at left edge');
                        }

                        // MOBILE FIX: Constrain settings icon container width
                        const settingsContainer = document.querySelector('#settings-icon-container');
                        if (settingsContainer) {
                            settingsContainer.style.maxWidth = '48px';
                            settingsContainer.style.width = 'auto';
                            console.log('[Mobile] Constrained settings icon container width');
                        }

                        // MOBILE FIX: Remove padding from settings icon HTML wrapper
                        const htmlContainer = document.querySelector('#settings-icon-container .html-container');
                        if (htmlContainer) {
                            htmlContainer.style.padding = '0';
                        }

                        // MOBILE FIX: Set input bar padding to 10px on both sides
                        // Use setTimeout to ensure it applies after Gradio's CSS
                        setTimeout(() => {
                            const component25 = document.querySelector('#component-25');
                            const component26 = document.querySelector('#component-26');
                            if (component25) {
                                component25.style.setProperty('padding-left', '10px', 'important');
                                component25.style.setProperty('padding-right', '10px', 'important');
                                console.log('[Mobile] Set component-25 padding to 10px with !important');
                            }
                            if (component26) {
                                component26.style.setProperty('padding-left', '10px', 'important');
                                component26.style.setProperty('padding-right', '10px', 'important');
                                console.log('[Mobile] Set component-26 padding to 10px with !important');
                            }
                        }, 100);
                    }
                }, 500);
            }
            """,
        )

    # Route 2: Settings page with BrowserState auto-load
    with demo.route("Settings", "settings") as settings_route:
        # Capture components returned from settings.render()
        (
            model_dropdown,
            temperature_slider,
            max_tokens_slider,
            theme_radio,
            context_name,
            context_url,
            context_description,
            settings_storage,  # BrowserState component
        ) = settings.render(config, user_state, settings_state)

        # Auto-load settings from BrowserState on page load
        # This is the elegant Gradio way - no JavaScript workarounds needed!
        @settings_route.load(
            inputs=[settings_storage],
            outputs=[
                model_dropdown,
                temperature_slider,
                max_tokens_slider,
                theme_radio,
                context_name,
                context_url,
                context_description,
            ],
        )
        def load_settings_from_browser(stored_settings: dict):
            """
            Load settings from BrowserState (localStorage) for guest users.

            For authenticated users, database persistence is primary.
            This only activates when no user is logged in.
            """
            if not stored_settings:
                # Return defaults if nothing in localStorage
                return [
                    "openrouter: gpt-5-mini",  # model_dropdown
                    0.2,  # temperature
                    1000,  # max_tokens
                    "Auto",  # theme
                    "",  # context_name
                    "",  # context_url
                    "",  # context_description
                ]

            # Extract model config
            model_config = stored_settings.get("model_config", {})
            provider = model_config.get("provider", "openrouter")
            model = model_config.get("model", "gpt-5-mini")
            model_display = f"{provider}: {model}"

            # Extract appearance
            appearance = stored_settings.get("appearance", {})
            theme = appearance.get("theme", "Auto")

            # Extract context
            context = stored_settings.get("context", {})

            return [
                model_display,  # ✅ Works for dropdowns!
                model_config.get("temperature", 0.2),
                model_config.get("max_tokens", 1000),
                theme,
                context.get("name", ""),
                context.get("url", ""),
                context.get("description", ""),
            ]

    return demo
