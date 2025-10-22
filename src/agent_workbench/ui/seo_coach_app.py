"""
Dutch SEO Coaching Interface - UI-002 SEO Coach Interface.
Complete SEO coach Gradio application with Dutch business forms and direct httpx
integration.
"""

import os
import uuid
from typing import Any, Dict

import gradio as gr
import httpx

from ..services.auth_service import AuthService
from .components.business_profile_form import (
    create_business_profile_dict,
    get_business_profile_form_components,
    validate_business_profile,
)
from .components.dutch_messages import get_dutch_message


def create_seo_coach_app() -> gr.Blocks:
    """
    Create Dutch SEO coaching interface with direct httpx integration.

    Returns:
        Gradio Blocks interface for SEO coaching
    """
    with gr.Blocks(
        title="AI SEO Coach - Nederlandse Bedrijven",
        theme=gr.themes.Soft(),
        css="""
        @import url('/static/assets/css/fonts.css');

        .business-panel { background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .coaching-panel { min-height: 500px; }
        .success { color: #155724; background: #d4edda; padding: 10px;
                   border-radius: 4px; }
        .error { color: #721c24; background: #f8d7da; padding: 10px;
                 border-radius: 4px; }
        .processing { color: #0c5460; background: #d1ecf1; padding: 10px;
                      border-radius: 4px; }
        """,
    ) as interface:

        # Header with settings button
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown("# 🚀 AI SEO Coach voor Nederlandse Bedrijven")
                gr.Markdown(
                    "*Verbeter je website ranking met persoonlijke AI coaching*"
                )
            settings_btn = gr.Button("⚙️ Instellingen", size="sm", scale=1)

        # State management (minimal, following UI-001 patterns)
        conversation_id = gr.State(str(uuid.uuid4()))
        business_profile = gr.State({})

        with gr.Row():
            # Left Panel: Business Profile
            with gr.Column(scale=1, elem_classes=["business-panel"]):
                gr.Markdown("### 🏢 Jouw Bedrijf")

                # Form components
                business_name, business_type, website_url, location = (
                    get_business_profile_form_components()
                )

                # Analysis button
                analyze_btn = gr.Button(
                    "🔍 Analyseer Mijn Website", variant="primary", size="lg"
                )

                # Status display
                gr.Markdown("### 📊 Status")
                analysis_status = gr.HTML(
                    value=(
                        "<div class='info'>Vul je bedrijfsgegevens in om "
                        "te beginnen</div>"
                    )
                )

                # Phase 2 feature stubs
                gr.Markdown("### 📄 Documenten (Binnenkort)")
                gr.File(label="Upload Document", interactive=False, visible=True)
                gr.HTML("<em>Document analyse komt beschikbaar in Phase 2</em>")

            # Right Panel: Coaching Chat
            with gr.Column(scale=2, elem_classes=["coaching-panel"]):
                gr.Markdown("### 💬 Je Persoonlijke SEO Coach")

                chatbot = gr.Chatbot(
                    height=450,
                    label="",
                    placeholder=get_dutch_message("coach_ready"),
                    type="messages",
                )

                with gr.Row():
                    message_input = gr.Textbox(
                        placeholder=get_dutch_message("message_placeholder"),
                        label=get_dutch_message("message_label"),
                        lines=2,
                        scale=4,
                    )

                    send_button = gr.Button(
                        get_dutch_message("send_button"), variant="primary", scale=1
                    )

                # Quick action buttons
                with gr.Row():
                    quick_audit = gr.Button(
                        get_dutch_message("quick_audit_title"), size="sm"
                    )
                    keyword_help = gr.Button(
                        get_dutch_message("keyword_help_title"), size="sm"
                    )
                    content_ideas = gr.Button(
                        get_dutch_message("content_ideas_title"), size="sm"
                    )

        # Event handlers with direct httpx integration
        analyze_btn.click(
            fn=_handle_website_analysis,
            inputs=[
                website_url,
                business_name,
                business_type,
                location,
                conversation_id,
            ],
            outputs=[chatbot, business_profile, analysis_status],
        )

        send_button.click(
            fn=_handle_coaching_message,
            inputs=[message_input, conversation_id, business_profile],
            outputs=[message_input, chatbot],
        )

        message_input.submit(
            fn=_handle_coaching_message,
            inputs=[message_input, conversation_id, business_profile],
            outputs=[message_input, chatbot],
        )

        # Quick actions
        quick_audit.click(
            fn=lambda conv_id, profile: _handle_quick_action("audit", conv_id, profile),
            inputs=[conversation_id, business_profile],
            outputs=[chatbot],
        )

        keyword_help.click(
            fn=lambda conv_id, profile: _handle_quick_action(
                "keywords", conv_id, profile
            ),
            inputs=[conversation_id, business_profile],
            outputs=[chatbot],
        )

        content_ideas.click(
            fn=lambda conv_id, profile: _handle_quick_action(
                "content", conv_id, profile
            ),
            inputs=[conversation_id, business_profile],
            outputs=[chatbot],
        )

        # Add authentication handler (on_load)
        # NOTE: Temporarily disabled until Phase 2.1 login UI is implemented
        # See: docs/architecture/decisions/UI-004-pwa-app-user-settings.md
        # When enabled, requires application-level auth (LoginButton),
        # not Space-level OAuth
        auth_mode = os.getenv(
            "AUTH_MODE", "disabled"
        )  # "disabled", "development", or "oauth"
        enable_auth = auth_mode in ["development", "oauth"]

        # TEMP: Force disable until login UI exists (Phase 2.1)
        enable_auth = False

        if enable_auth:
            print(f"🔐 [SEO Coach] Adding on_load auth handler (mode: {auth_mode})...")

            async def on_load(request: gr.Request):
                """Initialize user session on app load for SEO Coach.

                This handler is called when the Gradio interface loads.
                It creates or retrieves the user and manages session state.

                Supports two modes:
                - oauth: HuggingFace OAuth (production)
                - development: Local username-based auth (dev)
                """
                print("=" * 80)
                print(f"🔐 [SEO COACH] ON_LOAD - Authenticating (mode: {auth_mode})")
                print("=" * 80)

                try:
                    # Initialize auth service
                    auth_service = AuthService()

                    # Get or create user based on auth mode
                    if auth_mode == "development":
                        # Development mode: use local username
                        dev_username = os.getenv("DEV_USERNAME", "local-dev-user")

                        # Create mock request with username
                        class DevRequest:
                            def __init__(self, username):
                                self.username = username
                                self.email = f"{username}@localhost"
                                self.avatar_url = None
                                self.client = {"host": "127.0.0.1"}
                                self.headers = {"user-agent": "Development"}

                        dev_request = DevRequest(dev_username)
                        user = await auth_service.get_or_create_user_from_request(
                            request=dev_request, provider="development"
                        )
                        print(f"✅ Development user: {user.get('username')}")
                    else:
                        # OAuth mode: use HuggingFace OAuth
                        user = await auth_service.get_or_create_user_from_request(
                            request=request, provider="huggingface"
                        )
                        print(f"✅ User authenticated: {user.get('username')}")

                    # Check for active session (within last 30 min)
                    active_session = await auth_service.get_active_session(
                        user_id=user["id"], max_age_minutes=30
                    )

                    if active_session:
                        # Reuse existing session
                        session = active_session
                        await auth_service.update_session_activity(session["id"])
                        print(f"♻️  Reusing session: {session['id']}")
                    else:
                        # Create new session
                        session = await auth_service.create_session(
                            user_id=user["id"], request=request
                        )
                        print(f"🆕 Created new session: {session['id']}")

                    print(f"✅ Authentication complete for {user.get('username')}")

                except Exception as e:
                    print(f"❌ Authentication error: {e}")
                    import traceback

                    print(f"🎯 Traceback: {traceback.format_exc()}")

            # Wire up on_load event
            interface.load(fn=on_load, inputs=None, outputs=None)
            print("✅ [SEO Coach] on_load authentication handler wired")
        else:
            print("⚠️  [SEO Coach] Authentication disabled")

        # Settings navigation
        settings_btn.click(fn=None, js="window.location.href = '/settings'")

    return interface


async def _handle_website_analysis(
    url: str, biz_name: str, biz_type: str, location: str, conv_id: str
) -> tuple:
    """
    Handle website analysis with direct httpx integration.

    Args:
        url: Website URL
        biz_name: Business name
        biz_type: Business type
        location: Location
        conv_id: Conversation ID

    Returns:
        Tuple of (chat_history, business_profile, status_html)
    """
    # Validate inputs
    is_valid, error_msg = validate_business_profile(biz_name, biz_type, url, location)
    if not is_valid:
        return [], {}, f"<div class='error'>❌ {error_msg}</div>"

    try:
        # Create business profile
        profile = create_business_profile_dict(biz_name, biz_type, url, location)

        # Detect API port based on environment
        api_port = os.getenv("GRADIO_SERVER_PORT", "8000")
        api_base = f"http://localhost:{api_port}"

        # Direct httpx call to consolidated service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_base}/api/v1/chat/consolidated",
                json={
                    "user_message": (
                        f"Analyseer mijn {biz_type.lower()} website {url} "
                        f"voor SEO verbeteringen"
                    ),
                    "conversation_id": conv_id,
                    "workflow_mode": "seo_coach",
                    "business_profile": profile,
                    "streaming": False,
                },
            )
            response.raise_for_status()
            result = response.json()

        # Create initial chat history
        welcome_message = (
            f"Welkom {biz_name}! Ik heb je {biz_type.lower()} website " f"geanalyseerd."
        )
        chat_history = [
            {"role": "assistant", "content": welcome_message},
            {
                "role": "assistant",
                "content": result.get("assistant_response", ""),
            },
        ]

        # Success status
        success_html = f"""
        <div class='success'>
            ✅ {get_dutch_message('analysis_complete')}<br>
            <strong>Bedrijf:</strong> {biz_name}<br>
            <strong>Website:</strong> <a href='{url}' target='_blank'>{url}</a>
        </div>
        """

        return chat_history, profile, success_html

    except Exception as e:
        error_html = (
            f"<div class='error'>❌ {get_dutch_message('error_general')}: "
            f"{str(e)}</div>"
        )
        return [], {}, error_html


async def _handle_coaching_message(
    msg: str, conv_id: str, profile: Dict[str, Any]
) -> tuple:
    """
    Handle coaching conversation with direct httpx integration.

    Args:
        msg: User message
        conv_id: Conversation ID
        profile: Business profile

    Returns:
        Tuple of (empty_string, updated_chat_history)
    """
    if not msg.strip():
        return "", gr.update()

    if not profile:
        error_msg = get_dutch_message("no_business_profile")
        return "", [{"role": "assistant", "content": error_msg}]

    try:
        # Detect API port based on environment
        api_port = os.getenv("GRADIO_SERVER_PORT", "8000")
        api_base = f"http://localhost:{api_port}"

        # Direct httpx call to consolidated service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{api_base}/api/v1/chat/consolidated",
                json={
                    "user_message": msg,
                    "conversation_id": conv_id,
                    "workflow_mode": "seo_coach",
                    "business_profile": profile,
                    "streaming": False,
                },
            )
            response.raise_for_status()

        # Get updated chat history
        async with httpx.AsyncClient(timeout=30.0) as client:
            history_response = await client.get(
                f"{api_base}/api/v1/conversations/{conv_id}/state"
            )
            history_response.raise_for_status()
            history_data = history_response.json()

        updated_history = history_data.get("conversation_history", [])

        return "", updated_history

    except Exception as e:
        # Add error to current history
        current_history = []
        try:
            api_port = os.getenv("GRADIO_SERVER_PORT", "8000")
            api_base = f"http://localhost:{api_port}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                history_response = await client.get(
                    f"{api_base}/api/v1/conversations/{conv_id}/state"
                )
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    current_history = history_data.get("conversation_history", [])
        except Exception:
            pass

        current_history.extend(
            [
                {"role": "user", "content": msg},
                {
                    "role": "assistant",
                    "content": (f"{get_dutch_message('error_general')}: {str(e)}"),
                },
            ]
        )

        return "", current_history


async def _handle_quick_action(
    action_type: str, conv_id: str, profile: Dict[str, Any]
) -> gr.update:
    """
    Handle quick SEO action buttons.

    Args:
        action_type: Type of quick action ("audit", "keywords", "content")
        conv_id: Conversation ID
        profile: Business profile

    Returns:
        Updated chat history
    """
    messages = {
        "audit": (
            "Geef me een snelle SEO-check van mijn website. "
            "Wat zijn de 3 belangrijkste verbeterpunten?"
        ),
        "keywords": (
            "Help me goede zoekwoorden te vinden voor mijn bedrijf. "
            "Welke zoekwoorden gebruikt mijn doelgroep?"
        ),
        "content": (
            "Geef me 5 concrete content-ideeën voor mijn bedrijf "
            "die goed scoren in Google."
        ),
    }

    message = messages.get(action_type, messages["audit"])
    return await _handle_coaching_message(message, conv_id, profile)
