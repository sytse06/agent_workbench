# Cleanup & Refactoring Roadmap

**Based on:** Functional Architecture Scan (2025-10-05)
**Objective:** Reduce complexity, improve CRUD consistency, remove dead code

---

## 🎯 Priority Areas

### 1. CRITICAL: Consolidate Chat Endpoints ⚠️

**Problem:**
- 3 different chat endpoints with overlapping functionality
- Confusion about which to use when
- Duplicated logic across routes

**Current State:**
```
api/routes/
  ├─ chat.py              - Legacy chat routes
  ├─ direct_chat.py       - Direct LLM (bypasses workflows)
  └─ consolidated_chat.py - Workflow-based chat
```

**Recommendation:**
```
api/routes/
  ├─ chat.py              - REMOVE (legacy)
  ├─ chat_direct.py       - Rename: Simple LLM-only endpoint
  └─ chat_workflow.py     - Rename: Full LangGraph workflow
```

**Decision Needed:**
- [ ] Which chat endpoint is primary?
- [ ] Keep direct_chat for external clients only?
- [ ] Move all Gradio UI to direct service calls?

---

### 2. HIGH: Remove Unused UI Layer

**Problem:**
- `ui/app.py` contains full interface definition but is NOT USED
- Main.py contains actual interface (simplified version)
- Maintenance burden with two versions

**Files to Review:**
```
ui/app.py                    - NOT USED (bypassed by main.py)
ui/mode_factory.py           - USED (but could be simplified)
ui/components/*.py           - SOME USED (need audit)
```

**Action Items:**
- [ ] Delete `ui/app.py` or mark as deprecated
- [ ] Move used components to main.py or document clearly
- [ ] Simplify mode_factory or remove if only 2 modes

**Code Impact:** ~500 lines removed

---

### 3. HIGH: Consolidate Database Layer

**Problem:**
- Duplication between Hub DB and SQLite implementations
- AdaptiveDatabase has duplicate methods (_sqlite_* prefix)
- No common interface/protocol

**Current Architecture:**
```python
AdaptiveDatabase
  ├─ save_conversation()         # Dispatcher
  │   ├─ _sqlite_save_conversation()
  │   └─ hub_db.save_conversation()
  │
  ├─ get_conversation()          # Dispatcher
  │   ├─ _sqlite_get_conversation()
  │   └─ hub_db.get_conversation()
  └─ ...13 methods total
```

**Proposed Refactor:**
```python
# Protocol/Abstract Base
class DatabaseBackend(Protocol):
    def save_conversation(data: Dict) -> str
    def get_conversation(id: str) -> Optional[Dict]
    def list_conversations(mode: str, limit: int) -> List[Dict]
    ...

# Implementations
class SQLiteBackend(DatabaseBackend):
    ...

class HubBackend(DatabaseBackend):
    ...

# Adapter
class AdaptiveDatabase:
    def __init__(self, mode: str):
        if os.getenv("SPACE_ID"):
            self.backend = HubBackend()
        else:
            self.backend = SQLiteBackend()

    def save_conversation(self, data):
        return self.backend.save_conversation(data)
```

**Benefits:**
- 50% less code in AdaptiveDatabase
- Clear separation of concerns
- Easier to add new backends (Postgres, etc.)

**Effort:** Medium (~2-3 hours)

---

### 4. MEDIUM: Improve CRUD Consistency

**Problem:**
- Some routes call database directly
- Some go through service layer
- Inconsistent patterns across resources

**Current CRUD Patterns:**

#### Pattern A: Service Layer (Good ✅)
```python
# Route
@router.get("/conversations/{id}")
async def get_conversation(id: str):
    conversation = await conversation_service.get_by_id(id)
    return conversation

# Service
class ConversationService:
    def get_by_id(self, id):
        return db.get_conversation(id)
```

#### Pattern B: Direct DB Call (Bad ❌)
```python
# Route
@router.get("/conversations/{id}")
async def get_conversation(id: str):
    # Calling DB directly from route!
    hub_db = app.adaptive_db
    conversation = hub_db.get_conversation(id)
    return conversation
```

**Recommendation:**
- [ ] ALL routes must go through service layer
- [ ] Services contain business logic + DB calls
- [ ] Routes only validate + serialize

**Files to Refactor:**
```
api/routes/conversations.py  - Add ConversationService
api/routes/messages.py       - Add MessageService
api/routes/direct_chat.py    - Keep direct (by design)
```

---

### 5. MEDIUM: Clean Up Empty/Placeholder Classes

**Files with Empty Implementations:**

```python
# services/context_service.py
class ContextService:
    pass  # No methods!

# ui/components/simple_client.py
class SimpleLangGraphClient:
    def __init__(self):
        pass  # Placeholder
```

**Decision:**
- [ ] Implement ContextService properly
- [ ] OR remove and use Dict[str, Any] for context
- [ ] Remove SimpleLangGraphClient if unused

---

### 6. LOW: Reduce Test Duplication

**Current Stats:**
- 151 classes in main codebase
- 100+ test classes
- Some tests overlap (unit + integration)

**Action:**
- [ ] Audit test coverage report
- [ ] Remove redundant integration tests
- [ ] Focus on critical path coverage

---

## 📊 Estimated Impact

### Code Reduction
```
Unused UI files:        ~500 lines
Database duplication:   ~200 lines
Empty classes:          ~50 lines
Consolidated routes:    ~300 lines
─────────────────────────────────
Total removal:          ~1,050 lines (~8% of codebase)
```

### Complexity Reduction
```
Current:  151 classes, 84 functions
After:    ~130 classes, ~70 functions
Reduction: 14% fewer classes
```

### Files Removed
```
ui/app.py
ui/components/simple_client.py
api/routes/chat.py (legacy)
services/context_service.py (if not implemented)
```

---

## 🗺️ Execution Plan

### Phase 1: Quick Wins (1-2 days)
1. ✅ Document current architecture (DONE - this doc)
2. Delete `ui/app.py` (mark deprecated)
3. Remove empty `ContextService`
4. Remove `SimpleLangGraphClient`
5. Document chat endpoint strategy

**Deliverable:** 300-400 lines removed, no functionality change

### Phase 2: Database Refactor (2-3 days)
1. Create `DatabaseBackend` protocol
2. Implement `SQLiteBackend`
3. Implement `HubBackend`
4. Refactor `AdaptiveDatabase` to use backends
5. Update all service calls

**Deliverable:** Cleaner database abstraction

### Phase 3: Service Layer (3-4 days)
1. Create `ConversationService` (if missing)
2. Create `MessageService`
3. Refactor routes to use services
4. Remove direct DB calls from routes

**Deliverable:** Consistent CRUD patterns

### Phase 4: Route Consolidation (2-3 days)
1. Decide on chat endpoint strategy
2. Remove legacy `api/routes/chat.py`
3. Rename remaining chat routes for clarity
4. Update all imports

**Deliverable:** Clear API structure

---

## 🧪 Testing Strategy

### For Each Phase:
1. **Before refactor:** Run full test suite, note coverage
2. **During refactor:** Maintain green tests
3. **After refactor:** Verify same coverage %

### Critical Tests:
```bash
# Chat functionality
pytest tests/integration/test_chat.py -v

# Database operations
pytest tests/unit/test_database.py -v

# End-to-end
pytest tests/ui/test_dual_mode_integration.py -v
```

---

## 🎨 Architecture Goals (Post-Cleanup)

### Clear Layer Separation

```
┌─────────────────────────────────────┐
│  UI LAYER (Gradio)                  │
│  - main.py interface creation       │
│  - Event handlers                   │
└──────────────┬──────────────────────┘
               │ Direct service calls
               │ (no HTTP self-calls)
┌──────────────▼──────────────────────┐
│  API LAYER (FastAPI)                │
│  - REST endpoints for external use  │
│  - Validation & serialization       │
└──────────────┬──────────────────────┘
               │ Service layer calls
┌──────────────▼──────────────────────┐
│  SERVICE LAYER                      │
│  - Business logic                   │
│  - Workflow orchestration           │
│  - LLM provider management          │
└──────────────┬──────────────────────┘
               │ Repository calls
┌──────────────▼──────────────────────┐
│  REPOSITORY LAYER                   │
│  - DatabaseBackend protocol         │
│  - SQLiteBackend / HubBackend       │
└──────────────┬──────────────────────┘
               │ Model operations
┌──────────────▼──────────────────────┐
│  MODEL LAYER                        │
│  - Pydantic schemas                 │
│  - SQLAlchemy models                │
└─────────────────────────────────────┘
```

### Design Principles

1. **Single Responsibility**
   - Routes: Validation + serialization ONLY
   - Services: Business logic ONLY
   - Repositories: Data access ONLY

2. **Dependency Injection**
   - Services injected into routes
   - Repositories injected into services
   - No global state (except config)

3. **Interface Segregation**
   - Small, focused protocols
   - Backend-agnostic interfaces
   - Easy to mock/test

4. **DRY (Don't Repeat Yourself)**
   - No duplicate CRUD logic
   - Shared validation logic
   - Reusable service methods

---

## 📋 Checklist

### Before Starting
- [ ] Read Functional Architecture Scan
- [ ] Run full test suite (baseline)
- [ ] Create cleanup branch: `git checkout -b cleanup/architecture-refactor`

### Phase 1: Quick Wins
- [ ] Delete/deprecate `ui/app.py`
- [ ] Remove `ContextService` (or implement)
- [ ] Remove `SimpleLangGraphClient`
- [ ] Document chat endpoint strategy
- [ ] All tests still pass

### Phase 2: Database Refactor
- [ ] Create `DatabaseBackend` protocol
- [ ] Implement `SQLiteBackend`
- [ ] Implement `HubBackend`
- [ ] Refactor `AdaptiveDatabase`
- [ ] All tests still pass

### Phase 3: Service Layer
- [ ] Create/update `ConversationService`
- [ ] Create/update `MessageService`
- [ ] Refactor routes to use services
- [ ] All tests still pass

### Phase 4: Route Consolidation
- [ ] Decide chat endpoint strategy
- [ ] Remove legacy routes
- [ ] Rename remaining routes
- [ ] Update all imports
- [ ] All tests still pass

### After Completion
- [ ] Full test suite passes
- [ ] Code coverage maintained/improved
- [ ] Update architecture diagrams
- [ ] Merge to develop

---

## 🔗 Related Documents

- [Functional Architecture Scan](./FUNCTIONAL_ARCHITECTURE_SCAN.md)
- [File Upload README](./showcases/FILE_UPLOAD_README.md)
- Architecture decisions: `docs/architecture/decisions/`

---

**Last Updated:** 2025-10-05
**Next Review:** After Phase 1 completion
