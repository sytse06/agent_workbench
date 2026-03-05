# Common Development Patterns

## Adding a New LangGraph Workflow Node

```python
async def your_node(state: WorkbenchState) -> dict:
    user_msg = state["user_message"]
    mode = state["workflow_mode"]
    result = await process_something(user_msg, mode)
    return {
        "assistant_response": result,
        "workflow_steps": state["workflow_steps"] + ["your_node"],
        "execution_successful": True
    }
```

LangGraph merges the returned dict into state. No need to return full state.

## Working with the Bridge

```python
lg_state = await bridge.load_into_langgraph_state(
    conversation_id=conv_id, user_message="Hello", workflow_mode="workbench"
)
final_state = await workflow.ainvoke(lg_state)
await bridge.save_from_langgraph_state(final_state)
```

## Using AdaptiveDatabase

```python
db = AdaptiveDatabase(mode="workbench")  # Auto-detects environment
conversation = db.get_conversation(conversation_id)
db.save_message(message_data)
messages = db.get_messages(conversation_id)
```

## Adding a New UI Mode

1. Create interface in `ui/your_mode_app.py`
2. Register in `ui/mode_factory.py` mode_registry
3. Add mode-specific state fields to `WorkbenchState`
4. Add tests in `tests/ui/test_your_mode.py`

## Human-Steered Development Workflow

```bash
make arch TASK=CORE-002-feature-name      # 1. Architecture (human)
make feature TASK=CORE-002-feature-name   # 2. Implementation (AI)
make validate TASK=CORE-002-feature-name  # 3. Validation
make complete TASK=CORE-002-feature-name  # 4. Completion
```
