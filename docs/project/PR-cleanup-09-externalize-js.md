# PR-09: Externalize Inline JavaScript

**Branch:** `feature/cleanup-09-externalize-js`
**Status:** Done

## Problem

`mode_factory_v2.py` contained a 246-line inline JavaScript block passed to
`demo.load(fn=None, js=...)`. It was loaded unconditionally for both Workbench
and SEO Coach modes, even though Workbench is intended to be plain Gradio with
zero custom JS. The JS also contained 6 fragile `#component-N` selectors that
break whenever component render order changes.

## Changes

### New file: `src/agent_workbench/static/js/ui-init.js`
- Extracted 246-line JS block verbatim as a self-executing IIFE
- Replaced `#component-16` → `#aw-main`
- Replaced `#component-17` → `#aw-top-bar`
- Replaced `#component-25` + `#component-26` → `#aw-input-bar` (consolidated)

### `src/agent_workbench/ui/mode_factory_v2.py`
- Removed inline JS string and its `demo.load(fn=None, js=...)` call
- Added `"load_custom_js": True` to SEO Coach config
- Added `"load_custom_js": False` to Workbench config
- Added conditional script injection inside `build_gradio_app()`:
  - SEO Coach: injects `<script src="/static/js/ui-init.js">` on page load
  - Workbench: no JS injected, no request to `ui-init.js`

### `src/agent_workbench/ui/pages/chat.py`
- `gr.Column(scale=4, ...)` → `elem_id="aw-main"` (was `#component-16`)
- `gr.Row(agent-workbench-top-bar)` → `elem_id="aw-top-bar"` (was `#component-17`)
- `gr.Row(agent-workbench-input-bar)` → `elem_id="aw-input-bar"` (was `#component-25`/`#component-26`)

## Verification

```bash
make pre-commit && uv run pytest tests/ -q
# SEO Coach: sidebar toggle works, settings icon navigates, new-chat fires
# Workbench: browser Network tab shows no ui-init.js request
# Both: no #component-N selectors remain in JS
```

## Prerequisites for PR-10

The named `elem_id` values added here enable PR-10 to safely remove all
`#component-N` selectors from `styles.css`.
