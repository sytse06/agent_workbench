# PR-10: CSS Conditional Loading + Cleanup

**Branch:** `feature/cleanup-10-css-split`
**Status:** Done
**Depends on:** PR-09 (named elem_id selectors)

## Problem

- Both modes loaded the same 2,522-line CSS stack unconditionally
- `agent-workbench-design.css` (766 lines) was an exact duplicate of `tokens.css` — dead weight
- `fonts.css` (206 lines) manually loaded Google Fonts; now handled by `gr.themes.GoogleFont()`
- `styles.css` (1,152 lines) had heavy Gradio overrides, `#component-N` selectors, and
  font/color vars now covered by the Gradio theme system
- Workbench mode should be plain Gradio — no custom CSS, no custom JS

## Changes

### `src/agent_workbench/ui/mode_factory_v2.py`
- Workbench: `gr.themes.Base(primary_hue=blue, font=GoogleFont("Roboto"))`, `css=None`
- SEO Coach: `gr.themes.Base(primary_hue=emerald, font=GoogleFont("Open Sans"))`,
  `css=load_css(["tokens.css", "styles.css", "shared.css", "settings.css", "seo-coach.css"])`
- `fonts.css` dropped — `gr.themes.GoogleFont()` handles font loading for both modes
- `show_conv_browser=False` hardcoded for Workbench (was env-var driven)
- Added `load_css()` helper to concatenate CSS files from the assets/css directory
- Removed direct `tokens_css` / `styles_css` file reads from `build_gradio_app()`

### `src/agent_workbench/static/assets/css/agent-workbench-design.css` — DELETED
766 lines, confirmed exact duplicate of `tokens.css`. No references in Python code.

### `src/agent_workbench/static/assets/css/fonts.css` — DELETED
Font loading now handled by `gr.themes.GoogleFont()` in both theme configs.

### `src/agent_workbench/static/assets/css/main.css` — DELETED
Was an `@import` aggregator for `styles.css` + `agent-workbench-design.css`.
With Python-side conditional loading, this file is unused.

### `src/agent_workbench/static/assets/css/styles.css` — trimmed 1,152 → ~450 lines
- Removed `@import url('tokens.css')` (tokens loaded separately, before styles)
- Removed `#component-N` selectors — replaced by named `elem_id` from PR-09:
    `#component-14` → removed (was duplicate centering rule; `.agent-workbench-chat-container` handles it)
    `#component-16` → `#aw-main`
    `#component-17` → `#aw-top-bar`
    `#component-25`, `#component-26` → `#aw-input-bar`
    `#component-8` → removed (sidebar New Chat button; targeted by class `.sidebar-new-chat-btn`)
    `#component-5` → removed (outer Row; `.agent-workbench-chat-container` is sufficient)
    `#component-20` → removed (top-bar-right; already covered by `.agent-workbench-top-bar-right`)
- Removed font-family overrides (now handled by `gr.themes.GoogleFont()`)
- Removed typography section (body font, heading font, gradio-container font)

## Verification

```bash
make pre-commit && uv run pytest tests/ -q
# Workbench: stock Gradio look, blue theme, zero custom CSS/JS loaded
# SEO Coach: full branded look preserved (green theme, sidebar, styled icons)
```

## CSS file inventory after PR-10

| File | Lines | Status |
|------|-------|--------|
| `tokens.css` | 151 | Kept — CSS variables for SEO Coach |
| `styles.css` | ~450 | Trimmed — SEO Coach component styles |
| `shared.css` | 137 | Kept — functional layout (SEO Coach) |
| `settings.css` | 53 | Kept — settings page (SEO Coach) |
| `seo-coach.css` | 45 | Kept — SEO Coach panels |
| `agent-workbench-design.css` | 766 | **DELETED** (duplicate) |
| `fonts.css` | 206 | **DELETED** (replaced by gr.themes.GoogleFont) |
| `main.css` | 12 | **DELETED** (replaced by Python-side loading) |
