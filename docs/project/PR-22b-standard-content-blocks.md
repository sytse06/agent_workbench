# PR-2.2b: Standard Content Blocks + LangChain→Gradio Mapping Layer

**Branch:** `feature/standard-content-blocks`
**Status:** Planning
**Depends on:** PR-2.2 (merged)
**Precedes:** PR-2.3 (ContentRetriever — also modifies `agent_service.py`)

---

## Problem

### 1. `agent_service.py` uses manual, Anthropic-specific block parsing

The current streaming implementation:

```python
content = chunk.content
if isinstance(content, list):          # Anthropic-only assumption
    for block in content:
        block_type = block.get("type")
        if block_type == "thinking":   # Anthropic key
            text = block.get("thinking", "")
        elif block_type == "text":
            text = block.get("text", "")
elif isinstance(content, str):         # all other providers
    ...
```

Problems:
- `isinstance(content, list)` only fires for Anthropic extended thinking; OpenAI o-series
  reasoning blocks stream as `content` list too but with different keys (`"reasoning"` type,
  `"data"` field) — they fall through to the `str` branch and reasoning is lost
- Ollama reasoning models (deepseek-r1, qwq) embed thinking in `<think>` tags inside plain
  text — neither the old code nor this PR extracts them as structured blocks (out of scope;
  requires tag parsing, noted as a future PR)
- Doesn't use `chunk.content_blocks` — the standardized property available since
  `langchain-core 1.0`

### 2. `chat.py` constructs `gr.ChatMessage` directly in two places

The LangChain-event → Gradio mapping is duplicated raw in both handlers:
- `handle_chat_interface_message` (Workbench, ~line 1121)
- `handle_submit` (SEO Coach, ~line 516)

Each hardcodes `metadata` titles as plain strings with no symbol and in different
languages. There is no single source of truth for what a thinking bubble, tool call, or
file processing event looks like in the UI. Adding a new content block type (tool calls,
citations) in PR-2.3 or later means touching both handlers.

`message_converter.py` already exists as the right home for this logic but only covers
stored messages — not streaming events.

---

## `content_blocks` in `langchain-core 1.2.17`

Verified against installed version:

```python
# Plain text chunk
AIMessageChunk(content="hello").content_blocks
# → [{'type': 'text', 'text': 'hello'}]

# OpenAI o-series reasoning (standardized)
AIMessageChunk(content=[{'type': 'reasoning', 'data': '...'}]).content_blocks
# → [{'type': 'reasoning', 'data': '...'}]

# Anthropic extended thinking (NOT yet normalized — wrapped as non_standard)
AIMessageChunk(content=[{'type': 'thinking', 'thinking': '...'}]).content_blocks
# → [{'type': 'non_standard', 'value': {'type': 'thinking', 'thinking': '...'}}]

# Ollama plain text (all models)
AIMessageChunk(content="hello").content_blocks
# → [{'type': 'text', 'text': 'hello'}]  — works correctly

# Ollama reasoning models (deepseek-r1, qwq) — thinking is embedded in text, not structured
AIMessageChunk(content="<think>...</think>answer").content_blocks
# → [{'type': 'text', 'text': '<think>...</think>answer'}]  — tags not parsed
```

**Implication:** Anthropic `thinking` → `reasoning` normalization is not yet in 1.2.17.
The implementation must handle both `'reasoning'` (OpenAI) and `'non_standard'` with inner
`thinking` (Anthropic) as reasoning blocks. When LangChain normalizes this in a future
release, only the `non_standard` branch needs removal.

---

## Scope

**IN:**
- `agent_service.py`: Replace manual `chunk.content` parsing with `chunk.content_blocks`
  iteration; handle all three block types: `text`, `reasoning`, `non_standard`/`thinking`
- `ui/components/message_converter.py`: Add `_BLOCK_LABELS` symbol registry and
  `streaming_event_to_chat_messages()` — single function mapping SSE event dicts to
  `list[gr.ChatMessage]` with consistent symbols; covers all current event types and is
  extensible for PR-2.3 tool-call events
- `ui/pages/chat.py`: Replace duplicated `gr.ChatMessage` construction in both handlers
  with calls to `streaming_event_to_chat_messages()`

**OUT:**
- SSE protocol changes (event type names unchanged: `thinking_chunk`, `answer_chunk`,
  `done`, `processing_file`)
- Tool call event types — deferred to PR-2.3 (but `_BLOCK_LABELS` is designed for easy extension)
- Ollama `<think>` tag parsing — separate PR; requires text post-processing layer
- Upgrading `langchain-core` — 1.2.17 is the latest; no upgrade available

---

## Architecture

### `agent_service.py` — updated `astream()` block parsing

```python
async for chunk in model.astream(self._to_lc(messages)):
    for block in chunk.content_blocks:
        block_type = block.get("type")

        if block_type == "text":
            text = block.get("text", "")
            if text:
                answer_acc += text
                yield {"type": "answer_chunk", "content": text}

        elif block_type == "reasoning":
            # OpenAI o-series, Gemini (standardized in langchain-core 1.x)
            data = block.get("data", "")
            if data:
                thinking_acc += data
                yield {"type": "thinking_chunk", "content": data}

        elif block_type == "non_standard":
            # Anthropic extended thinking (not yet normalized in 1.2.17)
            inner = block.get("value", {})
            if inner.get("type") == "thinking":
                text = inner.get("thinking", "")
                if text:
                    thinking_acc += text
                    yield {"type": "thinking_chunk", "content": text}
```

When LangChain normalizes Anthropic thinking → `reasoning`, remove the `non_standard`
branch. No other changes needed.

### `message_converter.py` — symbol registry + `streaming_event_to_chat_messages()`

#### Symbol registry

```python
# Maps SSE event type → (symbol, label_en, label_nl)
# PR-2.3 adds "tool_call" and "tool_result" entries here — no other file changes needed.
_BLOCK_LABELS: dict[str, tuple[str, str, str]] = {
    "thinking_chunk":   ("🧠", "Thinking",    "Denken"),
    "processing_file":  ("📄", "Processing",  "Verwerken"),
    # PR-2.3 additions:
    # "tool_call":      ("🔍", "Retrieving",  "Ophalen"),
    # "tool_result":    ("📋", "Result",       "Resultaat"),
}
```

The symbol is prepended to the label: `"🧠 Thinking"`, `"📄 Processing report.pdf…"`.

#### `streaming_event_to_chat_messages()`

```python
def streaming_event_to_chat_messages(
    event: dict,
    thinking_content: str = "",
    answer_content: str = "",
    locale: str = "en",
) -> list[gr.ChatMessage]:
    """Map a streaming SSE event dict to a list of gr.ChatMessage for UI rendering.

    Args:
        event: SSE event dict with 'type' and optional 'content'/'filename' keys.
        thinking_content: Accumulated thinking text (updated externally by caller).
        answer_content: Accumulated answer text (updated externally by caller).
        locale: 'en' or 'nl' — selects label language from _BLOCK_LABELS.

    Returns:
        List of gr.ChatMessage to yield to the Gradio UI.
        Empty list if the event produces no visible output.
    """
    event_type = event.get("type")
    label_idx = 2 if locale == "nl" else 1

    if event_type == "processing_file":
        symbol, label_en, label_nl = _BLOCK_LABELS["processing_file"]
        label = label_nl if locale == "nl" else label_en
        fname = event.get("filename", "document")
        return [gr.ChatMessage(
            role="assistant",
            content="",
            metadata={"title": f"{symbol} {label} {fname}…", "status": "pending"},
        )]

    if event_type == "thinking_chunk":
        symbol, label_en, label_nl = _BLOCK_LABELS["thinking_chunk"]
        label = label_nl if locale == "nl" else label_en
        return [gr.ChatMessage(
            role="assistant",
            content=thinking_content,
            metadata={"title": f"{symbol} {label}", "status": "pending"},
        )]

    if event_type == "answer_chunk":
        symbol, label_en, label_nl = _BLOCK_LABELS["thinking_chunk"]
        label = label_nl if locale == "nl" else label_en
        msgs = []
        if thinking_content:
            msgs.append(gr.ChatMessage(
                role="assistant",
                content=thinking_content,
                metadata={"title": f"{symbol} {label}", "status": "done"},
            ))
        msgs.append(gr.ChatMessage(role="assistant", content=answer_content))
        return msgs

    return []
```

### `chat.py` — before/after

**Before (duplicated in both handlers):**
```python
elif event_type == "thinking_chunk":
    thinking_content += event.get("content", "")
    msgs = [gr.ChatMessage(
        role="assistant",
        content=thinking_content,
        metadata={"title": "Reasoning", "status": "pending"},   # no symbol, EN only
    )]
    yield msgs
elif event_type == "answer_chunk":
    answer_content += event.get("content", "")
    msgs = []
    if thinking_content:
        msgs.append(gr.ChatMessage(...metadata={"title": "Reasoning", "status": "done"}))
    msgs.append(gr.ChatMessage(role="assistant", content=answer_content))
    yield msgs
```

**After — Workbench handler:**
```python
elif event_type in ("thinking_chunk", "answer_chunk", "processing_file"):
    if event_type == "thinking_chunk":
        thinking_content += event.get("content", "")
    elif event_type == "answer_chunk":
        answer_content += event.get("content", "")
    msgs = streaming_event_to_chat_messages(
        event, thinking_content, answer_content, locale="en"
    )
    if msgs:
        yield msgs
```

**After — SEO Coach handler:** identical, `locale="nl"`.

---

## Step-by-Step Implementation

### Step 1: Update `agent_service.py`

Replace lines 106–128 in `astream()` with the `content_blocks` iteration shown above.

Run `uv run pytest tests/unit/services/test_agent_service.py -v` — all existing tests
must pass before moving on.

### Step 2: Update tests for `agent_service.py`

`tests/unit/services/test_agent_service.py` currently mocks raw `chunk.content`. Update
mocks to use actual `AIMessageChunk` objects so `content_blocks` is computed correctly:

- Plain text: `AIMessageChunk(content="hello")`
- Anthropic thinking: `AIMessageChunk(content=[{'type': 'thinking', 'thinking': '...'}])`
- OpenAI reasoning: `AIMessageChunk(content=[{'type': 'reasoning', 'data': '...'}])`
- Mixed: thinking block + text block in same chunk

Add new test: **OpenAI reasoning blocks** → `thinking_chunk` events (currently untested
and silently broken).

Add new test: **Ollama plain text** → only `answer_chunk` events, no `thinking_chunk`.

### Step 3: Add `_BLOCK_LABELS` and `streaming_event_to_chat_messages()` to `message_converter.py`

Implement as shown in the Architecture section.

### Step 4: Update `chat.py` — both handlers

Replace duplicated `gr.ChatMessage` construction blocks in:
1. `handle_chat_interface_message` (Workbench) — `locale="en"`
2. `handle_submit` (SEO Coach) — `locale="nl"`

Also update the final (non-streaming) `final_assistant` list at the end of each handler
to use the same function for consistency.

### Step 5: Tests

**`tests/unit/ui/test_message_converter.py`** — add tests for `streaming_event_to_chat_messages`:

- `processing_file` event, `locale="en"` → title contains `"📄"` and filename
- `processing_file` event, `locale="nl"` → title contains `"📄"` and Dutch label
- `thinking_chunk` event → title contains `"🧠"`, `status="pending"`
- `answer_chunk` with prior thinking → two messages: thinking (`status="done"`) + answer
- `answer_chunk` without prior thinking → single answer message, no thinking bubble
- Unknown event type → empty list

**`tests/unit/services/test_agent_service.py`** — update mocks (Step 2 above).

---

## Files Touched

| File | Change |
|---|---|
| `src/agent_workbench/services/agent_service.py` | Replace manual block parsing with `content_blocks` iteration |
| `src/agent_workbench/ui/components/message_converter.py` | Add `_BLOCK_LABELS` registry + `streaming_event_to_chat_messages()` |
| `src/agent_workbench/ui/pages/chat.py` | Replace duplicated ChatMessage construction in both handlers |
| `tests/unit/services/test_agent_service.py` | Update mocks; add OpenAI reasoning + Ollama tests |
| `tests/unit/ui/test_message_converter.py` | Add streaming event mapping tests |

No new dependencies. No DB changes. No API changes.

---

## Extending for PR-2.3

When PR-2.3 adds tool call events, only two things change in this file:

1. Uncomment (or add) entries in `_BLOCK_LABELS`:
   ```python
   "tool_call":   ("🔍", "Retrieving",  "Ophalen"),
   "tool_result": ("📋", "Result",       "Resultaat"),
   ```

2. Add handling in `streaming_event_to_chat_messages()` for the new event types.

No changes to `chat.py` or `agent_service.py` needed for the symbol/label layer.

---

## Verification

```bash
# After Step 1+2
uv run pytest tests/unit/services/test_agent_service.py -v

# After all steps
make pre-commit   # mypy, ruff, black, pytest must all pass

# Manual: verify thinking bubble symbol (Anthropic)
make start-app
# Enable extended thinking → submit message → "🧠 Thinking" bubble should appear

# Manual: verify Dutch labels (SEO Coach)
APP_MODE=seo_coach make start-app
# Submit message → "🧠 Denken" bubble in Dutch

# Manual: verify file processing symbol
# Attach a file → approve → "📄 Processing report.pdf…" bubble should appear

# Manual: verify OpenAI reasoning (if o-series model configured)
# Previously: reasoning silently dropped. After this PR: "🧠 Thinking" bubble appears.
```

---

## Relation to PR-2.3

PR-2.3 (ContentRetriever) adds a `tools` parameter to `agent_service.astream()`. That
change is orthogonal — it doesn't touch the block parsing logic changed here. Merge this
PR first so PR-2.3 starts from the cleaned-up base and only needs to add entries to
`_BLOCK_LABELS` for its new event types.

When LangChain normalizes Anthropic `thinking` → `reasoning` (expected in a future 1.x
release), remove the `non_standard` branch from `agent_service.py` — one block, one PR.
