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

/* Conversation list styling (Dataset component) */
#conv-list {
    margin-bottom: 0.5rem;
}

#conv-list .label {
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.25rem;
    color: var(--body-text-color);
}

/* Dataset table/list container */
#conv-list table {
    max-height: 500px;
    overflow-y: auto;
    border-radius: 6px;
    border: 1px solid var(--border-color-primary);
    width: 100%;
}

/* Individual conversation items (table rows) */
#conv-list tbody tr {
    cursor: pointer;
    transition: background-color 0.15s ease;
    border-bottom: 1px solid var(--border-color-primary);
}

#conv-list tbody tr td {
    padding: 0.75rem;
}

#conv-list tbody tr:hover {
    background-color: var(--background-fill-secondary);
}

#conv-list tbody tr:last-child {
    border-bottom: none;
}

#conv-list tbody tr.selected {
    background-color: var(--color-accent-soft);
    font-weight: 500;
}

/* Category header rows - visual styling only */
/* Headers are identified by 📅 emoji in text content */
/* Note: Non-clickable behavior handled in load_selected_conversation */

/* Responsive layout */
@media (max-width: 768px) {
    .chatbot-container {
        height: 400px !important;
    }

    .input-row {
        flex-direction: column;
    }

    #conv-list table {
        max-height: 300px;
    }

    #conv-list tbody tr td {
        padding: 0.5rem;
    }
}
"""
