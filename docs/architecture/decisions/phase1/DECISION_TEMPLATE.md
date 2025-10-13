# Architecture Decision: [TASK-ID] - [Brief Title]

## Status
[ ] SCOPING - Defining boundaries
[ ] DISCUSSING - Architectural options
[ ] DECIDED - Ready for implementation
[ ] IMPLEMENTED - Code complete

## Scope Definition (HUMAN CONTROLLED)
### What This Task Includes
- [ ] Specific requirement 1
- [ ] Specific requirement 2
- [ ] Specific requirement 3

### What This Task Explicitly Excludes
- ❌ Feature X (save for future iteration)
- ❌ Integration Y (separate task)
- ❌ Optimization Z (premature at this stage)

### Success Criteria (Must be measurable)
- [ ] Concrete outcome 1
- [ ] Concrete outcome 2
- [ ] Concrete outcome 3

## Implementation Boundaries for AI
### AI Should Implement
- Specific file: `src/agent_workbench/[module]/[file].py`
- Specific function signatures: `def process_document(doc: Document) -> ProcessedDocument`
- Specific test files: `tests/unit/test_[module].py`

### AI Should NOT Decide
- ❌ Adding new dependencies
- ❌ Changing existing interfaces
- ❌ Modifying database schema
- ❌ Adding new API endpoints not specified

## Implementation Handoff
### Exact Files to Create/Modify
- [ ] `src/agent_workbench/[module]/[file].py` - [Specific purpose]
- [ ] `tests/unit/test_[file].py` - [Specific test cases]

### Function Signatures (EXACT)
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Exact docstring describing behavior."""
    pass
```
