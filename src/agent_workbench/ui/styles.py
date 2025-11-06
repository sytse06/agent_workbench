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

/* Conversation dropdown styling */
#conv-dropdown {
    margin-bottom: 0.5rem;
}

#conv-dropdown label {
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.25rem;
    color: var(--body-text-color);
}

#conv-dropdown .wrap {
    border-radius: 6px;
    border: 1px solid var(--border-color-primary);
    transition: all 0.2s ease-in-out;
}

#conv-dropdown .wrap:hover {
    border-color: var(--border-color-accent);
}

#conv-dropdown .wrap:focus-within {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 3px var(--color-accent-soft);
}

#conv-dropdown input {
    font-size: 0.9rem;
    padding: 0.5rem;
}

#conv-dropdown .dropdown-container {
    max-height: 300px;
    overflow-y: auto;
    border-radius: 4px;
}

#conv-dropdown .dropdown-item {
    padding: 0.75rem;
    cursor: pointer;
    transition: background-color 0.15s ease;
    border-bottom: 1px solid var(--border-color-primary);
}

#conv-dropdown .dropdown-item:hover {
    background-color: var(--background-fill-secondary);
}

#conv-dropdown .dropdown-item:last-child {
    border-bottom: none;
}

#conv-dropdown .dropdown-item.selected {
    background-color: var(--color-accent-soft);
    font-weight: 500;
}

/* Responsive layout */
@media (max-width: 768px) {
    .chatbot-container {
        height: 400px !important;
    }

    .input-row {
        flex-direction: column;
    }

    #conv-dropdown .dropdown-container {
        max-height: 200px;
    }

    #conv-dropdown .dropdown-item {
        padding: 0.5rem;
    }
}
"""
