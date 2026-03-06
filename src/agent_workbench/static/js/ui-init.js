/**
 * ui-init.js — SEO Coach UI initialization
 *
 * Handles:
 * - Logo/chatbot visibility toggle (MutationObserver on message count)
 * - Sidebar toggle + mobile backdrop
 * - Mobile layout fixes
 * - Settings icon navigation
 * - New-chat button wiring
 *
 * Loaded conditionally for SEO Coach mode only.
 * Named elem_id selectors used throughout (no fragile #component-N IDs).
 */
(function () {
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

        console.log('[Sidebar] Toggle:', sidebarToggleBtn);
        console.log('[Sidebar] Column:', sidebarCol);
        console.log('[Sidebar] NewChat:', topBarNewChatBtn);
        console.log(
            '[Sidebar] NewChat classes:',
            topBarNewChatBtn?.className
        );

        // Debug: Check initial sidebar state
        console.log(
            '[Sidebar] Classes:', sidebarCol?.className
        );
        console.log(
            '[Sidebar] Hidden:',
            sidebarCol?.classList.contains(
                'conv-sidebar-hidden'
            )
        );

        // Ensure new chat icon visible when sidebar closed
        if (topBarNewChatBtn) {
            topBarNewChatBtn.classList.remove(
                'hidden-when-sidebar-open'
            );
            console.log(
                '[Sidebar] Init: visible,',
                topBarNewChatBtn.className
            );
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
                console.log(
                    '[Sidebar] Toggle, open:',
                    sidebarOpen
                );

                if (sidebarOpen) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            });
        } else {
            console.warn(
                '[Sidebar] Missing elements'
            );
            console.warn(
                '[Sidebar] toggle:', sidebarToggleBtn
            );
            console.warn(
                '[Sidebar] col:', sidebarCol
            );
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

        // MOBILE FIX: Full-width layout
        if (window.innerWidth <= 768) {
            const main = document.querySelector(
                'main.fillable'
            );
            if (main) {
                main.style.paddingLeft = '0';
                main.style.paddingRight = '0';
            }

            // Remove padding/margin from main chat column
            const awMain = document.querySelector(
                '#aw-main'
            );
            if (awMain) {
                awMain.style.paddingLeft = '0';
                awMain.style.paddingRight = '0';
                awMain.style.marginLeft = '0';
                awMain.style.marginRight = '0';
            }

            // Position top bar at left edge
            const topBar = document.querySelector(
                '#aw-top-bar'
            );
            if (topBar) {
                topBar.style.marginLeft = '0';
                topBar.style.marginRight = '0';
                topBar.style.position = 'relative';
                topBar.style.left = '0';
            }

            // Constrain settings icon width
            const sc = document.querySelector(
                '#settings-icon-container'
            );
            if (sc) {
                sc.style.maxWidth = '48px';
                sc.style.width = 'auto';
            }

            // Remove settings icon HTML padding
            const hc = document.querySelector(
                '#settings-icon-container '
                + '.html-container'
            );
            if (hc) {
                hc.style.padding = '0';
            }

            // Input bar padding (after Gradio CSS)
            setTimeout(() => {
                const inputBar = document.querySelector(
                    '#aw-input-bar'
                );
                if (inputBar) {
                    inputBar.style.setProperty(
                        'padding-left', '10px',
                        'important'
                    );
                    inputBar.style.setProperty(
                        'padding-right', '10px',
                        'important'
                    );
                }
            }, 100);
        }
    }, 500);
})();
