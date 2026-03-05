# Database Architecture: Protocol-Based Abstraction

```
Application Services
        |
AdaptiveDatabase (auto-selects backend)
        |
    +---+---+
    |       |
SQLiteBackend  HubBackend
    |           |
SQLAlchemy  HuggingFace Hub
```

## DatabaseBackend Protocol

**Location:** `database/protocol.py`

Operations: Conversation CRUD, Message CRUD, Business profile ops (SEO coach), Context ops.

## Backends

**SQLiteBackend** (`database/backends/sqlite.py`)
- SQLAlchemy async models, ThreadPoolExecutor bridge (async -> sync Protocol)
- Used in: local development, Docker

**HubBackend** (`database/backends/hub.py`)
- HuggingFace Datasets wrapper, simple delegation
- Used in: HuggingFace Spaces

**AdaptiveDatabase** (`database/adapter.py`)
- Environment detection: local/docker/hf_spaces
- Auto-selects appropriate backend

## Environment Detection

```python
SPACE_ID       -> hf_spaces -> HubBackend
/.dockerenv    -> docker    -> SQLiteBackend
default        -> local     -> SQLiteBackend
```
