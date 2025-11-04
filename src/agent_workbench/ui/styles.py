"""
Shared CSS for all modes.

Mode-specific differences (colors, fonts) are handled via Gradio theme configuration,
NOT via CSS. This ensures both modes have identical styling with only theme variations.
"""

SHARED_CSS = """
/* Hide Gradio's default route navigation bar (but NOT settings tabs) */
.gradio-container > nav,
.gradio-container > .tabs,
nav a[href^="/?"],
.header-links {
    display: none !important;
}

/* Chat page styles */
.chatbot-container {
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Settings page styles */
.settings-section {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    background: var(--background-fill-secondary);
}

.settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

/* Input field consistency */
.input-row {
    display: flex;
    gap: 0.5rem;
    align-items: flex-end;
}

/* Button styling */
.settings-button {
    min-width: 40px;
    padding: 0.5rem;
}

/* Responsive layout */
@media (max-width: 768px) {
    .chatbot-container {
        height: 400px !important;
    }

    .input-row {
        flex-direction: column;
    }
}
"""
