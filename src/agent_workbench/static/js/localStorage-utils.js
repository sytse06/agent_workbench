/**
 * localStorage Utility Functions for Agent Workbench
 *
 * Hybrid approach: gr.State + JavaScript localStorage
 * - gr.State: Session state (in-memory, resets on refresh)
 * - localStorage: Persistent storage (survives refresh/close)
 *
 * Storage Keys:
 * - agent_workbench_settings: User settings (model config, appearance, context)
 * - agent_workbench_conversations: Chat history (future implementation)
 */

const STORAGE_KEYS = {
    SETTINGS: 'agent_workbench_settings',
    CONVERSATIONS: 'agent_workbench_conversations',
    VERSION: 'agent_workbench_version'
};

const CURRENT_VERSION = '1.0.0';

/**
 * Save settings to localStorage
 * @param {Object} settings - Settings object to save
 * @returns {boolean} Success status
 */
function saveSettingsToLocalStorage(settings) {
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
}

/**
 * Load settings from localStorage
 * @returns {Object|null} Settings object or null if not found
 */
function loadSettingsFromLocalStorage() {
    try {
        const item = localStorage.getItem(STORAGE_KEYS.SETTINGS);
        if (!item) {
            console.log('[localStorage] No settings found');
            return null;
        }

        const data = JSON.parse(item);
        console.log('[localStorage] Loaded settings:', data.settings);

        // Version check (for future migrations)
        if (data.version !== CURRENT_VERSION) {
            console.warn('[localStorage] Version mismatch:', data.version, 'vs', CURRENT_VERSION);
        }

        return data.settings;
    } catch (error) {
        console.error('[localStorage] Failed to load settings:', error);
        return null;
    }
}

/**
 * Clear all Agent Workbench data from localStorage
 */
function clearAllLocalStorage() {
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
}

/**
 * Get localStorage usage info
 * @returns {Object} Usage statistics
 */
function getLocalStorageInfo() {
    try {
        let totalSize = 0;
        const items = {};

        Object.entries(STORAGE_KEYS).forEach(([name, key]) => {
            const item = localStorage.getItem(key);
            if (item) {
                const size = new Blob([item]).size;
                totalSize += size;
                items[name] = {
                    key: key,
                    size: size,
                    sizeKB: (size / 1024).toFixed(2)
                };
            }
        });

        return {
            totalSize: totalSize,
            totalSizeKB: (totalSize / 1024).toFixed(2),
            totalSizeMB: (totalSize / 1024 / 1024).toFixed(2),
            items: items,
            quota: '~5-10MB (browser dependent)'
        };
    } catch (error) {
        console.error('[localStorage] Failed to get info:', error);
        return null;
    }
}

// Export functions to window for Gradio JavaScript access
window.saveSettingsToLocalStorage = saveSettingsToLocalStorage;
window.loadSettingsFromLocalStorage = loadSettingsFromLocalStorage;
window.clearAllLocalStorage = clearAllLocalStorage;
window.getLocalStorageInfo = getLocalStorageInfo;

console.log('[localStorage] Utilities loaded successfully');
