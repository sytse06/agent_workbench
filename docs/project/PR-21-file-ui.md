# PR-2.1: File UI

**Branch:** `feature/file-ui`
**Status:** Planning

---

## Problem

Neither mode accepts file input. Users cannot attach documents to their messages — a core
requirement for SEO Coach (uploading terms, product pages, existing content) and Workbench
(uploading code files, configs, logs for analysis). The input bars in both modes use plain
`gr.Textbox`, which has no file handling capability.

This PR adds the file upload UI layer for both modes. No file processing happens here — that
is Phase 2.2 (Docling pipeline). The goal is: files can be attached, are visually confirmed,
and are stored as pending state ready for 2.2 to consume.

---

## Scope

**IN — Workbench:**
- Replace `gr.Textbox` with `gr.MultimodalTextbox` inside `gr.ChatInterface`
- Native upload button (paperclip icon, left of input) and native submit button (↑ arrow, right)
- Native drag-and-drop onto the input component
- File chip display above the text field (built-in Gradio behaviour)
- `handle_chat_interface_message` signature: `str` → `dict | str` via `_extract_message()`
- `pending_files` state variable populated on upload
- Approval dialog: `gr.Modal` shown on upload, auto-approves (stub)

**IN — SEO Coach:**
- Replace `gr.Textbox` with `gr.MultimodalTextbox(submit_btn=False)` in custom input bar
- Existing custom CSS submit button (`agent-workbench-submit-btn`) kept as-is
- Native upload button (paperclip, left), external submit button (right)
- Native drag-and-drop onto the input component
- File chip display above the text field (built-in Gradio behaviour)
- `handle_submit` signature: `str` → `dict | str` via `_extract_message()`
- `update_submit_button_state` updated: input is now a dict
- `pending_files` state variable populated on upload
- Approval dialog: same `gr.Modal`, same auto-approve stub
- Dutch labels: "Bestand toevoegen", "Verwijder", confirm/cancel in Dutch

**IN — Shared:**
- `_extract_message(input: str | dict) -> tuple[str, list]` utility (inline in `chat.py`)
- `pending_files` cleared on message submit (files forwarded as stub payload, not processed)
- Accepted file types: `.pdf`, `.docx`, `.txt`, `.md`
- Single file per message in this PR (`file_count="single"`)
- Tests for both modes

**OUT (subsequent PRs):**
- Docling conversion pipeline — PR-2.2
- Attaching file content to LLM messages — PR-2.2
- File storage and persistence — PR-2.2
- Multi-file upload — PR-2.2 decision
- File type validation beyond `file_types=` parameter
- Auth, PWA, user management — Phase 3

---

## Current State

**Workbench input bar:**
```python
gr.ChatInterface(
    fn=handle_chat_interface_message,
    textbox=gr.Textbox(
        placeholder=config["labels"]["placeholder"],
        submit_btn=True,
    ),
)
# handle_chat_interface_message(message: str, history, user_state, settings_state)
```

**SEO Coach input bar:**
```python
with gr.Row(elem_id="aw-input-bar", ...):
    textbox = gr.Textbox(
        placeholder=..., show_label=False, container=False,
        elem_classes=["agent-workbench-message-input"], scale=1,
    )
    submit_btn = gr.Button(value="", interactive=False, ...)
# handle_submit(message: str, history, user_state, settings_state)
# update_submit_button_state(text: str) -> gr.Button
```

---

## Architecture Decisions

### Decision 1: `gr.MultimodalTextbox` for both modes

`gr.MultimodalTextbox` is the only Gradio-native component that provides drag-and-drop,
file chip display, and an integrated upload button in a single component. `gr.UploadButton`
is click-to-pick only — no drag-and-drop support.

Both modes use the same component type. The difference is configuration:
- Workbench: `gr.MultimodalTextbox()` with `submit_btn` managed by `gr.ChatInterface`
- SEO Coach: `gr.MultimodalTextbox(submit_btn=False)` — external custom button kept

### Decision 2: Upload button icon is Gradio-native (paperclip)

`gr.MultimodalTextbox` renders a paperclip SVG on the left and an ↑ arrow on the right.
These are internal Gradio component icons — no CSS override needed, no Unicode workaround.
The ↑ arrow on the right is already the submit button in Workbench. For SEO Coach the
right-side button is the existing custom CSS button; `submit_btn=False` hides Gradio's own.

### Decision 3: Handler input becomes `dict | str`

`gr.MultimodalTextbox` passes `{"text": "...", "files": [...]}` to event handlers, vs.
plain `str` from `gr.Textbox`. A single utility function normalises both:

```python
def _extract_message(input: str | dict) -> tuple[str, list]:
    if isinstance(input, dict):
        return input.get("text", ""), input.get("files", [])
    return input, []
```

Both `handle_chat_interface_message` and `handle_submit` call this at entry. The rest of
each handler is unchanged. For PR-2.1 the files list is stored in state but not forwarded
to the agent — that wiring is PR-2.2.

### Decision 4: Approval dialog as `gr.Group(visible=False)` (auto-approve stub)

`gr.Modal` does not exist in Gradio 6.9.0. The approval UI is a `gr.Group(visible=False)`
positioned above the input bar, toggled to visible when a file is detected.

`gr.MultimodalTextbox` has no `.upload()` event — EVENTS are `['change', 'input', 'select',
'submit', 'focus', 'blur', 'stop']`. File detection is done in the `.change()` handler by
comparing the incoming `files` list against the previous `pending_files` state: if new files
arrived, show the approval group.

For PR-2.1 the approval group auto-approves: Confirm stores the file in `pending_files` and
hides the group; Cancel clears `pending_files` and hides the group. No real approval logic —
deferred to PR-2.2 when Docling determines what it can actually process.

---

## Step-by-Step Implementation

### Step 1: Replace input component — Workbench
**File:** `src/agent_workbench/ui/pages/chat.py`

Replace inside the `if not config.get("load_custom_js"):` block:

```python
# Before
textbox=gr.Textbox(
    placeholder=config["labels"]["placeholder"],
    submit_btn=True,
)

# After
textbox=gr.MultimodalTextbox(
    placeholder=config["labels"]["placeholder"],
    file_types=[".pdf", ".docx", ".txt", ".md"],
    file_count="single",
)
```

`gr.ChatInterface` handles the submit button automatically when `textbox` is
`gr.MultimodalTextbox` — no additional wiring needed.

Add `pending_files` state for Workbench:
```python
pending_files_wb = gr.State([])
```

### Step 2: Replace input component — SEO Coach
**File:** `src/agent_workbench/ui/pages/chat.py`

Replace inside the `gr.Row(elem_id="aw-input-bar")` block:

```python
# Before
textbox = gr.Textbox(
    placeholder=config["labels"]["placeholder"],
    show_label=False, container=False,
    elem_classes=["agent-workbench-message-input"], scale=1,
)

# After
textbox = gr.MultimodalTextbox(
    placeholder=config["labels"]["placeholder"],
    show_label=False, container=False,
    elem_classes=["agent-workbench-message-input"],
    scale=1,
    file_types=[".pdf", ".docx", ".txt", ".md"],
    file_count="single",
    submit_btn=False,   # keep external custom submit button
)
```

Add `pending_files` state for SEO Coach:
```python
pending_files_seo = gr.State([])
```

### Step 3: Update `_extract_message` utility + handler signatures
**File:** `src/agent_workbench/ui/pages/chat.py`

Add at module level (before the render functions):
```python
def _extract_message(input: str | dict) -> tuple[str, list]:
    if isinstance(input, dict):
        return input.get("text", ""), input.get("files", [])
    return input, []
```

Update `handle_chat_interface_message` (Workbench):
```python
def handle_chat_interface_message(
    message: str | dict,
    history: list,
    user_state: ...,
    settings_state: ...,
):
    text, files = _extract_message(message)
    # rest of handler uses `text` where `message` was used before
```

Update `handle_submit` (SEO Coach):
```python
def handle_submit(
    message: str | dict,
    history: ...,
    user_state: ...,
    settings_state: ...,
):
    text, files = _extract_message(message)
    if not text.strip():
        return
    # rest of handler uses `text` where `message` was used before
```

Update `update_submit_button_state` (SEO Coach — currently wired to `textbox.change()`):
```python
def update_submit_button_state(input: str | dict) -> gr.Button:
    text, _ = _extract_message(input)
    if text.strip():
        return gr.Button(..., interactive=True, ...)
    else:
        return gr.Button(..., interactive=False, ...)
```

### Step 4: Approval dialog (auto-approve stub)
**File:** `src/agent_workbench/ui/pages/chat.py`

`gr.Modal` does not exist in Gradio 6.9.0. Use `gr.Group(visible=False)` above the input bar:

```python
with gr.Group(visible=False, elem_classes=["aw-approval-bar"]) as approval_group:
    with gr.Row():
        approval_filename = gr.Markdown("")
        approve_btn = gr.Button(
            config["labels"].get("file_approve", "Confirm"), variant="primary", size="sm"
        )
        cancel_btn = gr.Button(
            config["labels"].get("file_cancel", "Remove"), size="sm"
        )
```

`gr.MultimodalTextbox` has no `.upload()` event. Wire `.change()` to detect new files by
comparing against `pending_files` state:

```python
def on_input_change(input_val: dict | str, pending: list) -> tuple:
    _, files = _extract_message(input_val)
    # New file detected: show approval group
    if files and files != pending:
        filename = files[0].get("orig_name", files[0].get("name", "unknown"))
        return gr.Group(visible=True), pending, f"**{filename}**"
    # File removed via chip ×: hide approval group, clear pending
    if not files and pending:
        return gr.Group(visible=False), [], ""
    return gr.Group(visible=False), pending, ""

textbox.change(
    fn=on_input_change,
    inputs=[textbox, pending_files],
    outputs=[approval_group, pending_files, approval_filename],
)

approve_btn.click(
    fn=lambda inp, _: (gr.Group(visible=False), _extract_message(inp)[1]),
    inputs=[textbox, pending_files],
    outputs=[approval_group, pending_files],
)

cancel_btn.click(
    fn=lambda: (gr.Group(visible=False), []),
    outputs=[approval_group, pending_files],
)
```

### Step 5: Add labels to mode configs
**File:** `src/agent_workbench/ui/mode_factory_v2.py` (or wherever mode config dicts live)

Workbench:
```python
"file_approval_title": "File attached",
"file_approve": "Confirm",
"file_cancel": "Remove",
```

SEO Coach (Dutch):
```python
"file_approval_title": "Bestand toegevoegd",
"file_approve": "Bevestigen",
"file_cancel": "Verwijder",
```

### Step 6: Clear pending files on submit
In both `handle_chat_interface_message` and `handle_submit`, clear the pending files
state at the end of a successful submit. The files are passed as stub metadata in the
payload (log only — PR-2.2 will wire the actual content):

```python
# In handle_submit, final yield:
yield (new_history, "", gr.Button(...), [])   # last [] clears pending_files
# Add pending_files to outputs list
```

### Step 7: Tests

**New file:** `tests/unit/ui/test_file_upload.py`

Workbench mode:
- `_extract_message` returns `(text, [])` for plain string input
- `_extract_message` returns `(text, files)` for dict input
- `handle_chat_interface_message` accepts dict input without raising
- `handle_chat_interface_message` accepts plain string input without raising (backwards compat)
- Upload event populates `pending_files` state
- Cancel button clears `pending_files` state

SEO Coach mode:
- `handle_submit` accepts dict input without raising
- `handle_submit` accepts plain string input without raising (backwards compat)
- `update_submit_button_state` returns inactive button when dict has empty text
- `update_submit_button_state` returns active button when dict has non-empty text
- Upload event populates `pending_files` state
- Cancel button clears `pending_files` state

---

## Files Touched

| File | Change |
|---|---|
| `src/agent_workbench/ui/pages/chat.py` | `gr.Textbox` → `gr.MultimodalTextbox` (both modes); `_extract_message` utility; handler signatures; approval dialog; pending_files state |
| `src/agent_workbench/ui/mode_factory_v2.py` | Add file-related labels to both mode configs |
| `tests/unit/ui/test_file_upload.py` | **NEW** — upload UI unit tests, separate checks for both modes |

---

## Verification

### Pre-merge checklist

**Shared:**
- [ ] `make pre-commit` passes (mypy, ruff, black, pytest)
- [ ] `_extract_message` handles both `str` and `dict` input
- [ ] Existing chat tests still pass (no regressions on string input path)

**Workbench mode:**
- [ ] `make start-app` — paperclip icon visible left of input, ↑ arrow visible right
- [ ] Click paperclip → file picker opens, `.pdf` / `.docx` / `.txt` / `.md` selectable
- [ ] Drag a file from Finder onto the input area → file chip appears above text field
- [ ] File chip shows filename + remove (×) button
- [ ] Approval modal appears after file attach, confirm/cancel buttons work
- [ ] Cancel removes file chip and clears pending state
- [ ] Type a message with file attached → submit works, no crash
- [ ] Streaming still works after component switch (tokens arrive progressively)
- [ ] Multi-turn chat still works (no history regression)

**SEO Coach mode:**
- [ ] `APP_MODE=seo_coach make start-app` — paperclip icon visible left, custom ↑ button visible right
- [ ] Click paperclip → file picker opens, same accepted types
- [ ] Drag a file from Finder onto the input area → file chip appears above text field
- [ ] File chip shows filename + remove (×) button
- [ ] Approval modal appears in Dutch ("Bestand toegevoegd", "Bevestigen", "Verwijder")
- [ ] Cancel removes file chip and clears pending state
- [ ] Submit button state (disabled/active/processing) still works with dict input
- [ ] Type a message with file attached → submit works, no crash
- [ ] Streaming still works after component switch (tokens arrive progressively)
- [ ] Dutch responses still produced (no mode regression)

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `gr.MultimodalTextbox` `container=False` may not render cleanly in SEO Coach's custom `gr.Row` | Test visually; fall back to `container=True` with CSS override if needed |
| SEO Coach's `submit_btn=False` may not fully hide Gradio's built-in submit button | Add `display: none` CSS targeting the hidden submit button's class if it still renders |
| `gr.ChatInterface` internal wiring may break when `textbox` type changes | Run `test_gradio_unified.py` (6 tests) after Step 1 before proceeding |
| `.change()` fires on every keystroke — approval group may flicker on text input | Guard with `if files and files != pending` (already in `on_input_change`); test with fast typing |
| File dict key for filename may vary (`name` vs `orig_name` vs `path`) | Check both keys: `files[0].get("orig_name", files[0].get("name", "unknown"))` |
