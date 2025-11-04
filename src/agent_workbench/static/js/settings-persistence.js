/**
 * Settings Persistence for Guest Users
 *
 * Handles saving/loading user settings to/from localStorage for non-authenticated users.
 * Authenticated users use database storage via UserSettingsService.
 */

const SETTINGS_STORAGE_KEY = 'agent_workbench_settings';

/**
 * Get default settings structure
 */
function getDefaultSettings() {
    return {
        model_config: {
            provider: "openrouter",
            model: "openai/gpt-4o-mini",
            temperature: 0.7,
            max_tokens: 2000
        },
        appearance: {
            theme: "Auto"
        },
        context: {
            name: "",
            url: "",
            description: ""
        }
    };
}

/**
 * Save settings to localStorage
 * Called from settings page save button for guest users
 */
function saveSettingsToLocalStorage(settings) {
    try {
        const settingsJson = JSON.stringify(settings);
        localStorage.setItem(SETTINGS_STORAGE_KEY, settingsJson);
        console.log('[Settings] Saved to localStorage:', settings);
        return true;
    } catch (error) {
        console.error('[Settings] Failed to save to localStorage:', error);
        return false;
    }
}

/**
 * Load settings from localStorage
 * Called on app initialization for guest users
 */
function loadSettingsFromLocalStorage() {
    try {
        const settingsJson = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (settingsJson) {
            const settings = JSON.parse(settingsJson);
            console.log('[Settings] Loaded from localStorage:', settings);
            return settings;
        }
    } catch (error) {
        console.error('[Settings] Failed to load from localStorage:', error);
    }

    // Return defaults if not found or error
    const defaults = getDefaultSettings();
    console.log('[Settings] Using default settings');
    return defaults;
}

/**
 * Clear settings from localStorage
 */
function clearSettingsFromLocalStorage() {
    try {
        localStorage.removeItem(SETTINGS_STORAGE_KEY);
        console.log('[Settings] Cleared from localStorage');
        return true;
    } catch (error) {
        console.error('[Settings] Failed to clear from localStorage:', error);
        return false;
    }
}

/**
 * Initialize settings on page load
 * Auto-navigates to chat page if on root
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Settings] Initializing settings system');

    // Ensure we start on chat page (root route)
    if (window.location.pathname === '/' || window.location.pathname === '') {
        console.log('[Settings] On root path, chat page should be visible');
    }

    // Load settings for guest users on app start
    // This will be called by Gradio's load event via Python
    window.agentWorkbenchSettings = {
        save: saveSettingsToLocalStorage,
        load: loadSettingsFromLocalStorage,
        clear: clearSettingsFromLocalStorage,
        getDefaults: getDefaultSettings
    };

    console.log('[Settings] Settings system ready');
});

/**
 * Export functions for use in Gradio JavaScript blocks
 */
window.saveSettingsToLocalStorage = saveSettingsToLocalStorage;
window.loadSettingsFromLocalStorage = loadSettingsFromLocalStorage;
window.clearSettingsFromLocalStorage = clearSettingsFromLocalStorage;
