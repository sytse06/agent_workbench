"""
Minimal localStorage utility for Gradio client-side state persistence.

This module provides reusable JavaScript functions for persisting Gradio state
to browser localStorage, enabling guest user settings persistence without a database.

⚠️ CRITICAL GRADIO LIMITATION (v5.43.1+):
    Direct .then() chains with inputs=[gr.State] DO NOT WORK for localStorage saves.
    Must use "hidden trigger pattern" instead:
        1. Create hidden gr.Textbox(visible=False)
        2. .then() to convert state to JSON and write to textbox
        3. textbox.change() to write JSON to localStorage

Usage Pattern:
    1. Include JS_LOCALSTORAGE_UTILS in a gr.HTML component at demo level
    2. Use save_to_localstorage_via_trigger() with hidden textbox pattern
    3. Use load_from_localstorage_js() in route.load() events to populate forms

Architecture Context:
    - Phase 2 UI-005: Settings persistence for guest users
    - Hybrid approach: gr.State (in-memory) + localStorage (persistent)
    - Future extensibility: Can be extended for chat history, themes, etc.

Gradio Limitations Addressed:
    - gr.State resets on page refresh
    - .then() events don't pass gr.State to JavaScript reliably
    - .change() events don't fire when JavaScript updates outputs
    - Solution: Hidden trigger textbox + JSON serialization

Reference:
    - Phase 2 UI-005 implementation: src/agent_workbench/ui/pages/settings.py:510-565
    - docs/architecture/decisions/UI-005-settings-page.md (lines 88-112)
    - Gradio client-side functions: https://www.gradio.app/guides/client-side-functions
"""

# Storage key constants
STORAGE_KEY_SETTINGS = "agent_workbench_settings"
STORAGE_KEY_CONVERSATIONS = "agent_workbench_conversations"
STORAGE_VERSION = "1.0.0"

# JavaScript utility functions (to be inlined in gr.HTML at demo level)
JS_LOCALSTORAGE_UTILS = """
<script>
    // localStorage Utility Functions (Agent Workbench)
    const STORAGE_KEYS = {
        SETTINGS: 'agent_workbench_settings',
        CONVERSATIONS: 'agent_workbench_conversations',
        VERSION: 'agent_workbench_version'
    };

    const CURRENT_VERSION = '1.0.0';

    window.saveSettingsToLocalStorage = function(settings) {
        try {
            const data = {
                version: CURRENT_VERSION,
                timestamp: new Date().toISOString(),
                settings: settings
            };
            localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(data));
            console.log('[localStorage] Saved settings:', settings);
            return true;
        } catch (error) {
            console.error('[localStorage] Failed to save settings:', error);
            return false;
        }
    };

    window.loadSettingsFromLocalStorage = function() {
        try {
            const item = localStorage.getItem(STORAGE_KEYS.SETTINGS);
            if (!item) {
                console.log('[localStorage] No settings found');
                return null;
            }

            const data = JSON.parse(item);
            console.log('[localStorage] Loaded settings:', data.settings);

            if (data.version !== CURRENT_VERSION) {
                console.warn(
                    '[localStorage] Version mismatch:',
                    data.version, 'vs', CURRENT_VERSION
                );
            }

            return data.settings;
        } catch (error) {
            console.error('[localStorage] Failed to load settings:', error);
            return null;
        }
    };

    window.clearAllLocalStorage = function() {
        try {
            Object.values(STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
            console.log('[localStorage] Cleared all data');
            return true;
        } catch (error) {
            console.error('[localStorage] Failed to clear data:', error);
            return false;
        }
    };

    console.log('[localStorage] Utilities loaded successfully (demo level)');
</script>
"""


def save_to_localstorage_js(storage_key: str = STORAGE_KEY_SETTINGS) -> str:
    """
    ⚠️ DEPRECATED: This pattern doesn't work in Gradio 5.43.1+

    The .then() chain with inputs=[settings_state, user_state] never executes
    properly. Use save_to_localstorage_via_trigger() instead.

    See: https://github.com/gradio-app/gradio/issues/...
    """
    return """
    function(settings_state, user_state) {
        console.error('[localStorage] DEPRECATED: Use hidden trigger pattern instead');
        return null;
    }
    """


def save_to_localstorage_via_trigger(storage_key: str = STORAGE_KEY_SETTINGS) -> str:
    """
    Generate JavaScript to save settings from a hidden trigger textbox.

    ⚠️ IMPORTANT: Gradio's .then() chain doesn't reliably pass gr.State as inputs
    to JavaScript functions. This pattern uses a hidden textbox as a trigger instead.

    Working Pattern (3 steps):
        1. Create hidden textbox to act as trigger
        2. Use .then() to convert settings_state to JSON and write to trigger
        3. Use .change() on trigger to write JSON to localStorage

    Example:
        import json

        # Step 1: Create hidden trigger
        settings_json_trigger = gr.Textbox(visible=False)

        # Step 2: Save button -> convert to JSON -> trigger
        save_event = save_btn.click(
            fn=save_settings_wrapper,
            inputs=[user_state, model_dropdown, ...],
            outputs=[success_msg, error_msg, settings_state],
        )

        save_event.then(
            fn=lambda settings, user: (
                json.dumps(settings) if (not user or not user.get("user_id")) else ""
            ),
            inputs=[settings_state, user_state],
            outputs=[settings_json_trigger],  # Write to trigger
        )

        # Step 3: Trigger change -> write to localStorage
        settings_json_trigger.change(
            fn=None,
            js=save_to_localstorage_via_trigger(),
            inputs=[settings_json_trigger],
            outputs=[],
        )

    Why This Works:
        - .then() CAN pass outputs to other components (like Textbox)
        - .change() DOES fire when component value changes via .then()
        - JavaScript receives JSON string (not Python dict)
        - Parse JSON string to restore object

    Args:
        storage_key: localStorage key (default: STORAGE_KEY_SETTINGS)

    Returns:
        JavaScript function string for .change() event on trigger textbox

    Reference:
        - Phase 2 UI-005 implementation (settings.py:510-565)
        - Gradio GitHub issue: .then() with gr.State inputs doesn't execute
    """
    return f"""
    function(settings_json) {{
        console.log('[Settings] Trigger fired with:', settings_json);

        // Empty string means user is authenticated (skip localStorage)
        if (!settings_json) {{
            console.log('[Settings] Empty trigger - user authenticated');
            return;
        }}

        try {{
            const settings = JSON.parse(settings_json);
            const data = {{
                version: '1.0.0',
                timestamp: new Date().toISOString(),
                settings: settings
            }};
            localStorage.setItem('{storage_key}', JSON.stringify(data));
            console.log('[Settings] Saved to localStorage:', settings);
        }} catch (error) {{
            console.error('[Settings] Failed to save to localStorage:', error);
        }}
    }}
    """


def load_from_localstorage_js(
    storage_key: str = STORAGE_KEY_SETTINGS,
    output_count: int = 8,
) -> str:
    """
    Generate JavaScript to load settings from localStorage and populate form.

    Use this in a route.load() event to restore settings when navigating to page.

    Example:
        with demo.route("Settings", "settings") as settings_demo:
            settings_components = settings.render(config, user_state, settings_state)
            form_components = settings_components[:-1]

            settings_demo.load(
                fn=None,
                js=load_from_localstorage_js(output_count=len(form_components) + 1),
                outputs=form_components + (settings_state,),
            )

    Args:
        storage_key: localStorage key (default: STORAGE_KEY_SETTINGS)
        output_count: Number of outputs to return (form fields + settings_state)

    Returns:
        JavaScript function string for Gradio route.load() event

    Note:
        This function assumes a specific settings structure:
        {
            model_config: {provider, model, temperature, max_tokens},
            appearance: {theme},
            context: {name, url, description}
        }

        Customize the extraction logic for different data structures.
    """
    return f"""
    async function() {{
        console.log('[Settings Load] Starting localStorage load');

        try {{
            const item = localStorage.getItem('{storage_key}');
            if (!item) {{
                console.log('[Settings Load] No settings found in localStorage');
                // Return proper defaults (not null) to avoid TypeError in sliders
                return [
                    'openrouter: gpt-5-mini',  // model_dropdown default
                    0.7,                        // temperature_slider default
                    2000,                       // max_tokens_slider default
                    'Auto',                     // theme_dropdown default
                    '',                         // context_name default
                    '',                         // context_url default
                    '',                         // context_description default
                    {{}}                        // settings_state default
                ];
            }}

            const data = JSON.parse(item);
            const settings = data.settings || {{}};
            console.log('[Settings Load] Loaded settings:', settings);

            // Extract model config
            const modelConfig = settings.model_config || {{}};
            const provider = modelConfig.provider || 'openrouter';
            const model = modelConfig.model || 'gpt-5-mini';
            const temperature = modelConfig.temperature || 0.7;
            const maxTokens = modelConfig.max_tokens || 2000;

            // Map provider:model to display name
            const modelDisplay = `${{provider}}: ${{model}}`;
            console.log('[Settings Load] Model display:', modelDisplay);

            // Extract appearance
            const appearance = settings.appearance || {{}};
            const theme = appearance.theme || 'Auto';

            // Extract context
            const context = settings.context || {{}};
            const contextName = context.name || '';
            const contextUrl = context.url || '';
            const contextDesc = context.description || '';

            // Return values for all form components in order:
            // [model_dropdown, temperature, max_tokens, theme,
            //  name, url, desc, settings_state]
            return [
                modelDisplay,      // model_dropdown
                temperature,       // temperature_slider
                maxTokens,         // max_tokens_slider
                theme,             // theme_dropdown
                contextName,       // context_name textbox
                contextUrl,        // context_url textbox
                contextDesc,       // context_description textarea
                settings           // settings_state (for save functionality)
            ];
        }} catch (error) {{
            console.error('[Settings Load] Failed to load settings:', error);
            // Return proper defaults (not null) to avoid TypeError in sliders
            return [
                'openrouter: gpt-5-mini',  // model_dropdown default
                0.7,                        // temperature_slider default
                2000,                       // max_tokens_slider default
                'Auto',                     // theme_dropdown default
                '',                         // context_name default
                '',                         // context_url default
                '',                         // context_description default
                {{}}                        // settings_state default
            ];
        }}
    }}
    """


# Future extensibility hooks (documented for reuse)
# ------------------------------------------------------------------------------
# When implementing additional localStorage features (e.g., chat history,
# theme preferences, UI state), follow the HIDDEN TRIGGER PATTERN:
#
# 1. Add new STORAGE_KEY constant (e.g., STORAGE_KEY_CHAT_HISTORY)
# 2. Add corresponding window function in JS_LOCALSTORAGE_UTILS
# 3. Create save/load helper functions following save_to_localstorage_via_trigger()
# 4. Document the data structure in the function docstring
#
# Example future additions:
# - save_chat_history_via_trigger() / load_chat_history_js()
# - save_theme_preference_via_trigger() / load_theme_preference_js()
# - save_ui_state_via_trigger() / load_ui_state_js()
#
# ⚠️ CRITICAL: Always use the hidden trigger pattern for saving:
#   1. Create hidden gr.Textbox(visible=False)
#   2. .then() to convert state to JSON and write to textbox
#   3. textbox.change() to write JSON to localStorage
#
# Direct .then() with inputs=[gr.State] DOES NOT WORK in Gradio 5.43.1+
# See save_to_localstorage_via_trigger() for working example.
# ------------------------------------------------------------------------------
