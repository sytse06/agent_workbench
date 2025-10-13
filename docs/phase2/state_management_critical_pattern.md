# Phase 2 State Management: Critical Pattern

**Date:** 2025-10-12
**Priority:** CRITICAL
**Purpose:** Explicitly define state ownership to prevent conflicts between LangGraph StateGraph and LangChain v1 create_agent

---

## Executive Summary

⚠️ **CRITICAL DECISION**: LangGraph StateGraph is the **SINGLE SOURCE OF TRUTH** for **conversation state** in Phase 2.

**The Problem:**
- LangChain v1's `create_agent()` has its own state management via `checkpointer`
- LangGraph StateGraph also manages state via nodes
- **Risk:** Two competing conversation history systems could conflict

**The Solution (Revised):**
- ✅ LangGraph StateGraph owns **conversation state** (history, user context, final results)
- ✅ LangChain agent CAN have **internal working state** via checkpointer during task execution
- ✅ When agent completes, its results are fed into LangGraph state
- ✅ Clear responsibility: Agent's checkpointer = working memory, LangGraph state = conversation record

**The Key Insight:**
An agent processing a complex task needs working memory - like notes while solving a problem. This internal state is ephemeral and task-specific. Once the task completes, the **results** flow into LangGraph's conversation state. No conflict exists because they serve different purposes.

---

## State Ownership Rules

### Rule 1: LangGraph StateGraph is the State Owner

```python
# ✅ CORRECT: LangGraph owns state
class WorkflowState(TypedDict):
    """LangGraph state - SINGLE SOURCE OF TRUTH."""
    conversation_id: UUID
    user_message: str
    user_id: UUID
    user_settings: Dict[str, Any]
    conversation_history: List[StandardMessage]
    agent_response: Optional[str]
    structured_response: Optional[AgentResponse]
    execution_successful: bool

# LangGraph workflow
builder = StateGraph(WorkflowState)
builder.add_node("execute_agent", execute_agent_node)
workflow = builder.compile(
    checkpointer=MemorySaver()  # ← ONLY LangGraph has checkpointer
)
```

### Rule 2: LangChain Agent Can Have Internal Working State

```python
# ✅ CORRECT: Agent CAN have checkpointer for internal working state
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

agent = create_agent(
    model=get_model(),
    tools=tools,
    middleware=[...],
    structured_output=AgentResponse,
    checkpointer=MemorySaver()  # ✅ ALLOWED for agent's internal working memory
)

# Purpose: Agent's checkpointer stores INTERNAL state during task execution
# - Tool calls made
# - Intermediate reasoning steps
# - Planning state
# - Progress tracking
#
# This is EPHEMERAL working memory - discarded after task completes
# Final results are extracted and fed into LangGraph state
```

**What Agent State Contains:**
- Internal reasoning steps (chain of thought)
- Tool execution history within this specific task
- Planning and re-planning state
- Error recovery attempts
- Progress through multi-step tasks

**What Agent State Does NOT Contain:**
- Full conversation history (that's in LangGraph state)
- User preferences (passed in via parameters)
- Previous conversation turns (provided by LangGraph node)

**Key Distinction:**
- **Agent checkpointer** = Working memory for the current task
- **LangGraph state** = Persistent conversation record

### Rule 3: Agent Executes Within LangGraph Node with Task-Scoped State

```python
# ✅ CORRECT: Agent runs inside LangGraph node with working memory
async def execute_agent_node(state: WorkflowState) -> dict:
    """
    LangGraph node that executes agent with internal working state.

    CRITICAL FLOW:
    1. Extract conversation history from LangGraph state
    2. Agent uses internal checkpointer for working memory during task
    3. Extract final results from agent
    4. Feed results back into LangGraph state
    """

    # 1. Extract data from LangGraph state
    conversation_history = state["conversation_history"]
    user_message = state["user_message"]
    user_settings = state["user_settings"]
    conversation_id = state["conversation_id"]

    # 2. Build agent input with conversation context
    agent_input = {
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ] + [
            {"role": "user", "content": user_message}
        ]
    }

    # 3. Execute agent with TASK-SCOPED working state
    # Agent's checkpointer tracks internal work for THIS TASK ONLY
    # Use task-specific thread_id (not conversation_id)
    import uuid
    task_id = str(uuid.uuid4())  # Unique ID for this agent task

    config = {
        "configurable": {
            "thread_id": task_id  # Agent's working memory for this task
        }
    }

    result = await agent.ainvoke(agent_input, config=config)
    # Agent's internal state (tool calls, reasoning) stored under task_id
    # This state is ephemeral - only used during task execution

    # 4. Extract structured response (final result)
    structured = result["structured_response"]

    # 5. Return updates - LangGraph merges into CONVERSATION state
    return {
        "agent_response": structured.message,
        "structured_response": structured,
        "conversation_history": state["conversation_history"] + [
            StandardMessage(
                role="assistant",
                content=structured.message,
                metadata={
                    "status": structured.status,
                    "task_id": task_id  # Track which agent task produced this
                }
            )
        ],
        "execution_successful": structured.status == "success"
    }
    # Agent's internal working state (task_id) can now be garbage collected
    # What matters is the final result, now in LangGraph state
```

**Key Points:**
- Agent gets unique `task_id` for its internal working memory
- Agent's checkpointer stores tool calls, reasoning under this `task_id`
- Final results extracted and fed into LangGraph's **conversation state**
- Agent's internal state is ephemeral - only for duration of task
- Conversation state (LangGraph) is persistent - survives across tasks

---

## State Flow Pattern

### Complete State Flow (Phase 2)

```
1. User Input
   └─> Gradio UI

2. API Request
   └─> POST /api/v1/chat/workflow

3. Load State (LangGraph Bridge)
   ├─> Load conversation from DB
   ├─> Load user settings from DB
   └─> Build WorkflowState
       └─> LangGraph StateGraph OWNS conversation state

4. Execute LangGraph Workflow
   ├─> Node 1: process_input
   │   └─> Returns dict → LangGraph MERGES into state
   │
   ├─> Node 2: prepare_agent_input
   │   └─> Returns dict → LangGraph MERGES into state
   │
   ├─> Node 3: execute_agent ⚠️ CRITICAL NODE
   │   ├─> Extract conversation_history FROM state
   │   ├─> Execute agent WITH internal working state (task-scoped)
   │   │   ├─> Agent uses checkpointer for working memory (task_id)
   │   │   ├─> Agent tracks tool calls, reasoning internally
   │   │   └─> Agent completes task
   │   ├─> Extract structured response (final result)
   │   └─> Returns dict → LangGraph MERGES into state
   │       └─> State now has updated conversation_history
   │       └─> Agent's internal state (task_id) is ephemeral
   │
   └─> Node 4: format_output
       └─> Returns dict → LangGraph MERGES into state

5. Save State (LangGraph Bridge)
   ├─> Extract final WorkflowState (conversation state)
   ├─> Convert to ConversationState
   └─> Save to DB
   └─> Agent's internal state NOT saved (ephemeral)

6. Return Response
   └─> API response with structured_response
```

---

## Implementation Examples

### Example 1: Agent Service (With Internal Working State)

```python
# services/agent_service.py

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, List

class AgentService:
    """
    Agent service with internal working state.

    CRITICAL: This service does NOT manage conversation state.
    - Agent CAN have checkpointer for internal working memory during task execution
    - Agent receives conversation history as input
    - Agent returns results; LangGraph manages conversation state persistence
    - Agent's internal state is task-scoped and ephemeral
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None

    async def initialize(self, mcp_server_configs: Dict[str, Dict]):
        """Initialize agent with internal working state."""

        # Load MCP tools
        mcp_client = MultiServerMCPClient(mcp_server_configs)
        tools = await mcp_client.get_tools()

        # Create agent WITH checkpointer for internal working memory
        self.agent = create_agent(
            model=get_model(),
            tools=tools,
            middleware=[
                PIIRedactionMiddleware(patterns=["email", "phone"]),
                SummarizationMiddleware(
                    model=get_model(),
                    max_tokens_before_summary=8000
                ),
                ContextMiddleware(db=self.db),
            ],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()  # ✅ Internal working state
        )

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str  # Unique ID for this task's working memory
    ) -> Dict[str, Any]:
        """
        Execute agent with conversation history.

        Args:
            messages: Full conversation history (from LangGraph state)
            user_settings: User preferences (from LangGraph state)
            task_id: Unique ID for task-scoped working memory

        Returns:
            Dict with structured_response

        CRITICAL:
        - Agent receives ALL context via messages parameter
        - Agent uses checkpointer for internal working memory (task_id)
        - Agent does NOT load or save conversation history
        - Agent's working state is ephemeral (task-scoped)
        """

        # Execute agent with task-scoped working memory
        config = {
            "configurable": {
                "thread_id": task_id  # Task-scoped working memory
            }
        }

        result = await self.agent.ainvoke(
            {
                "messages": messages,
                "config": user_settings
            },
            config=config
        )

        # Return result - LangGraph will update conversation state
        # Agent's internal state (task_id) remains in checkpointer but is ephemeral
        return result
```

### Example 2: LangGraph Workflow (State Owner)

```python
# services/workflow_orchestrator.py

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Dict, Any

class WorkflowState(TypedDict):
    """LangGraph state - SINGLE SOURCE OF TRUTH."""
    # User context
    user_id: UUID
    user_settings: Dict[str, Any]

    # Conversation
    conversation_id: UUID
    user_message: str
    conversation_history: List[StandardMessage]

    # Agent execution
    agent_response: Optional[str]
    structured_response: Optional[AgentResponse]

    # Workflow tracking
    steps: List[str]
    execution_successful: bool

class WorkflowOrchestrator:
    """
    LangGraph workflow orchestrator.

    CRITICAL: This class OWNS state management.
    Agent service is called from node but does NOT manage state.
    """

    def __init__(
        self,
        db: AdaptiveDatabase,
        agent_service: AgentService
    ):
        self.db = db
        self.agent_service = agent_service

        # Build workflow with LangGraph checkpointer
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with state persistence."""

        builder = StateGraph(WorkflowState)

        # Add nodes
        builder.add_node("process_input", self._process_input_node)
        builder.add_node("prepare_agent_input", self._prepare_agent_input_node)
        builder.add_node("execute_agent", self._execute_agent_node)
        builder.add_node("format_output", self._format_output_node)

        # Define flow
        builder.add_edge(START, "process_input")
        builder.add_edge("process_input", "prepare_agent_input")
        builder.add_edge("prepare_agent_input", "execute_agent")
        builder.add_edge("execute_agent", "format_output")
        builder.add_edge("format_output", END)

        # Compile with LangGraph checkpointer
        # CRITICAL: ONLY LangGraph has checkpointer
        return builder.compile(
            checkpointer=MemorySaver()  # ← State persistence here
        )

    async def _execute_agent_node(self, state: WorkflowState) -> Dict:
        """
        Execute agent with internal working state within LangGraph node.

        CRITICAL PATTERN:
        1. Extract conversation history FROM LangGraph state
        2. Generate task-specific ID for agent's working memory
        3. Execute agent with internal working state (task-scoped)
        4. Return updates TO state (LangGraph merges conversation state)
        5. Agent's internal state (task_id) is ephemeral
        """

        steps = state.get("steps", [])
        steps.append("Executing agent")

        try:
            # 1. Extract conversation history from LangGraph state
            conversation_history = state["conversation_history"]
            user_message = state["user_message"]
            user_settings = state["user_settings"]

            # 2. Build messages list for agent
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation_history
            ] + [
                {"role": "user", "content": user_message}
            ]

            # 3. Generate task-specific ID for agent's working memory
            import uuid
            task_id = str(uuid.uuid4())

            # 4. Execute agent with internal working state
            # Agent uses checkpointer for working memory (task_id)
            # Agent receives full context via messages parameter
            # Agent does NOT load/save conversation history
            result = await self.agent_service.run(
                messages=messages,
                user_settings=user_settings,
                task_id=task_id  # Task-scoped working memory
            )

            # 5. Extract structured response (final result)
            structured = result["structured_response"]

            # 6. Create new message for conversation history
            assistant_message = StandardMessage(
                role="assistant",
                content=structured.message,
                tool_calls=structured.tool_calls if structured.tool_calls else None,
                metadata={
                    "status": structured.status,
                    "reasoning": structured.reasoning,
                    "task_id": task_id  # Track which task produced this
                }
            )

            # 7. Return updates - LangGraph MERGES into CONVERSATION state
            # Agent's internal state (task_id) remains in checkpointer but is ephemeral
            return {
                "agent_response": structured.message,
                "structured_response": structured,
                "conversation_history": conversation_history + [assistant_message],
                "execution_successful": structured.status == "success",
                "steps": steps + ["Agent execution completed"]
            }
            # Agent's working memory (task_id) can now be garbage collected

        except Exception as e:
            # Error handling - still return state update
            return {
                "agent_response": None,
                "structured_response": AgentResponse(
                    status="error",
                    message=f"Agent execution failed: {str(e)}"
                ),
                "execution_successful": False,
                "steps": steps + [f"Agent execution failed: {str(e)}"]
            }

    async def execute(
        self,
        conversation_id: UUID,
        user_id: UUID,
        user_message: str
    ) -> WorkflowState:
        """
        Execute workflow with LangGraph state management.

        CRITICAL: LangGraph manages state through entire workflow.
        """

        # Load initial state from database
        user_settings = await self.db.get_user_settings_dict(user_id)
        conversation = await self.db.get_conversation(str(conversation_id))
        history = await self.db.get_messages(str(conversation_id))

        # Build initial LangGraph state
        initial_state: WorkflowState = {
            "user_id": user_id,
            "user_settings": user_settings,
            "conversation_id": conversation_id,
            "user_message": user_message,
            "conversation_history": [
                StandardMessage(**msg) for msg in history
            ],
            "agent_response": None,
            "structured_response": None,
            "steps": ["Workflow started"],
            "execution_successful": False
        }

        # Execute workflow - LangGraph manages state
        config = {"configurable": {"thread_id": str(conversation_id)}}
        final_state = await self.workflow.ainvoke(initial_state, config)

        return final_state
```

### Example 3: Bridge Integration

```python
# services/langgraph_bridge.py

class LangGraphStateBridge:
    """
    Bridge between database and LangGraph state.

    CRITICAL: Bridge loads/saves state for LangGraph.
    Agent does NOT interact with bridge directly.
    """

    async def load_into_langgraph_state(
        self,
        conversation_id: UUID,
        user_id: UUID,
        user_message: str
    ) -> WorkflowState:
        """
        Load state from DB into LangGraph format.

        Returns WorkflowState that LangGraph will manage.
        """

        # Load from database
        user_settings = await self.db.get_user_settings_dict(user_id)
        messages = await self.db.get_messages(str(conversation_id))

        # Build LangGraph state
        return {
            "user_id": user_id,
            "user_settings": user_settings,
            "conversation_id": conversation_id,
            "user_message": user_message,
            "conversation_history": [
                StandardMessage(**msg) for msg in messages
            ],
            "agent_response": None,
            "structured_response": None,
            "steps": [],
            "execution_successful": False
        }

    async def save_from_langgraph_state(
        self,
        state: WorkflowState
    ) -> None:
        """
        Save state from LangGraph to DB.

        Extracts conversation_history from LangGraph state
        and persists to database.
        """

        conversation_id = state["conversation_id"]
        conversation_history = state["conversation_history"]

        # Save only NEW messages to database
        existing_count = await self.db.get_message_count(str(conversation_id))
        new_messages = conversation_history[existing_count:]

        for msg in new_messages:
            await self.db.save_message({
                "conversation_id": str(conversation_id),
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata
            })
```

---

## Why This Pattern is Critical

### Problem: Conflicting Conversation State

If both LangGraph AND agent try to manage **conversation state** (history):

```python
# ❌ WRONG PATTERN - CONVERSATION STATE CONFLICT

# LangGraph manages conversation state
workflow = builder.compile(checkpointer=MemorySaver())

# Agent ALSO tries to manage conversation state with same thread_id
agent = create_agent(
    model=get_model(),
    tools=tools,
    checkpointer=MemorySaver()
)

# Inside node - using conversation_id for both!
config = {"configurable": {"thread_id": str(conversation_id)}}
result = await agent.ainvoke(messages, config=config)  # ❌ CONFLICT!

# Problem: Which conversation history is correct?
# - LangGraph state says conversation has 10 messages
# - Agent state says conversation has 8 messages
# - Database is out of sync with both
# → DATA CORRUPTION
```

### Solution: Separate Responsibilities

```python
# ✅ CORRECT PATTERN - CLEAR SEPARATION

# LangGraph owns CONVERSATION state (persistent)
workflow = builder.compile(
    checkpointer=MemorySaver()  # Conversation state persisted here
)

# Agent can have INTERNAL WORKING state (ephemeral)
agent = create_agent(
    model=get_model(),
    tools=tools,
    checkpointer=MemorySaver()  # ✅ Working memory for tasks
)

# Inside node - use TASK ID not conversation ID
import uuid
task_id = str(uuid.uuid4())  # Unique per task
config = {"configurable": {"thread_id": task_id}}  # ✅ Task-scoped
result = await agent.ainvoke(messages, config=config)

# Extract results and update LangGraph conversation state
return {
    "conversation_history": state["conversation_history"] + [new_message],
    "structured_response": result["structured_response"]
}
# Agent's working memory (task_id) is ephemeral - not saved to DB

# Result:
# - LangGraph state = SINGLE SOURCE OF TRUTH for conversation
# - Agent working memory = ephemeral task-scoped state
# - No conflict because they serve different purposes
# - Database syncs with LangGraph conversation state only
# → CONSISTENT STATE
```

**Key Distinction:**
- **LangGraph checkpointer** (conversation_id): Persistent conversation history
- **Agent checkpointer** (task_id): Ephemeral working memory for current task
- **Database**: Syncs with LangGraph conversation state only

---

## Phase 2 State Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio UI                            │
│            (User Input: "Analyze this code")            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              POST /api/v1/chat/workflow                 │
│            (API Request with user_id)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            LangGraphStateBridge.load()                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Load from DB:                                   │   │
│  │ - user_settings (provider, model, temp)         │   │
│  │ - conversation_history (all past messages)      │   │
│  │ - user profile                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                      │                                  │
│                      ▼                                  │
│              Build WorkflowState                        │
│         ┌──────────────────────────┐                    │
│         │ user_id: UUID            │                    │
│         │ user_settings: {...}     │                    │
│         │ conversation_history: [] │                    │
│         │ user_message: "..."      │                    │
│         └──────────────────────────┘                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          LangGraph StateGraph Workflow                  │
│        (SINGLE SOURCE OF TRUTH FOR STATE)               │
│                                                         │
│  ┌────────────────────────────────────────────────┐    │
│  │ WorkflowState (TypedDict)                      │    │
│  │  - LangGraph owns this state                   │    │
│  │  - All nodes update this state                 │    │
│  │  - checkpointer: MemorySaver()                 │    │
│  └────────────────────────────────────────────────┘    │
│                     │                                   │
│                     ▼                                   │
│         Node 1: process_input                           │
│            └─> Returns dict → LangGraph MERGES          │
│                     │                                   │
│                     ▼                                   │
│         Node 2: prepare_agent_input                     │
│            └─> Returns dict → LangGraph MERGES          │
│                     │                                   │
│                     ▼                                   │
│         Node 3: execute_agent ⚠️ CRITICAL               │
│         ┌─────────────────────────────────────┐         │
│         │ def execute_agent_node(state):      │         │
│         │   # Extract FROM state              │         │
│         │   history = state["conv_history"]   │         │
│         │   settings = state["user_settings"] │         │
│         │                                     │         │
│         │   # Call STATELESS agent            │         │
│         │   result = agent.ainvoke({          │         │
│         │     "messages": history             │         │
│         │   })                                │         │
│         │                                     │         │
│         │   # Return TO state                 │         │
│         │   return {                          │         │
│         │     "structured_response": result,  │         │
│         │     "conversation_history": [       │         │
│         │       ...history,                   │         │
│         │       new_message                   │         │
│         │     ]                               │         │
│         │   }                                 │         │
│         └─────────────────────────────────────┘         │
│                     │                                   │
│                     ▼                                   │
│             LangGraph MERGES dict                       │
│              into WorkflowState                         │
│         ┌──────────────────────────┐                    │
│         │ conversation_history:    │                    │
│         │   [..., assistant_msg]   │                    │
│         │ structured_response: {}  │                    │
│         └──────────────────────────┘                    │
│                     │                                   │
│                     ▼                                   │
│         Node 4: format_output                           │
│            └─> Returns dict → LangGraph MERGES          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           LangGraphStateBridge.save()                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Save to DB:                                     │   │
│  │ - Extract conversation_history from state       │   │
│  │ - Save NEW messages only                        │   │
│  │ - Update conversation metadata                  │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              API Response                               │
│  { structured_response: AgentResponse(...) }            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
                 Gradio UI


┌────────────────────────────────────────────────────────┐
│      AGENT WITH WORKING STATE (Inside Node 3)         │
│      ───────────────────────────────────────           │
│                                                        │
│    agent = create_agent(                              │
│        model=get_model(),                             │
│        tools=mcp_tools,                               │
│        middleware=[...],                              │
│        checkpointer=MemorySaver()  # ✅ Working state │
│    )                                                  │
│                                                        │
│    Agent receives:                                    │
│      - messages (conversation history)                │
│      - user_settings (config)                         │
│      - task_id (unique per task)                      │
│                                                        │
│    Agent's internal working memory:                   │
│      - Tool calls made                                │
│      - Reasoning steps                                │
│      - Planning state                                 │
│      - Progress tracking                              │
│      Stored in checkpointer under task_id             │
│                                                        │
│    Agent returns:                                     │
│      - structured_response (final result)             │
│                                                        │
│    Agent does NOT:                                    │
│      - Load conversation history from DB              │
│      - Save conversation history to DB                │
│      - Manage persistent conversation state           │
│                                                        │
│    Key: Working memory is EPHEMERAL (task-scoped)     │
│         Conversation state is PERSISTENT (LangGraph)  │
└────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

### ✅ DO

1. ✅ Give LangGraph StateGraph a checkpointer for conversation state (persistent)
2. ✅ Agent CAN have checkpointer for internal working memory (ephemeral)
3. ✅ Use unique task_id for agent's working state (NOT conversation_id)
4. ✅ Pass conversation history to agent via parameters
5. ✅ Return agent results, let LangGraph update conversation state
6. ✅ Save conversation state to database after workflow completes
7. ✅ Let agent's internal state be ephemeral (task-scoped)

### ❌ DON'T

1. ❌ Don't use conversation_id as agent's thread_id (creates conflict)
2. ❌ Don't let agent load conversation history from DB
3. ❌ Don't let agent save conversation history to DB
4. ❌ Don't persist agent's internal working state to DB
5. ❌ Don't modify conversation state outside LangGraph nodes
6. ❌ Don't confuse working memory (ephemeral) with conversation state (persistent)

---

## Summary

**State Ownership:**
- **LangGraph StateGraph**: OWNS conversation state (persistent), has checkpointer with conversation_id
- **LangChain Agent**: CAN have internal working state (ephemeral), checkpointer with task_id
- **Database**: Syncs with LangGraph conversation state only (NOT agent working state)

**Critical Pattern:**
```
User Input
  → Bridge loads conversation state from DB
  → LangGraph StateGraph manages conversation state (checkpointer: conversation_id)
    → Node generates unique task_id
    → Node calls agent with working memory (checkpointer: task_id)
    → Agent processes with internal working state
    → Agent returns final result
    → Node updates LangGraph conversation state
    → Agent's working state (task_id) is ephemeral
  → Bridge saves conversation state to DB (NOT agent working state)
  → API response
```

**Key Distinction:**
- **Conversation state** (LangGraph): Persistent, conversation_id, saved to DB
- **Working memory** (Agent): Ephemeral, task_id, NOT saved to DB

This pattern ensures:
✅ Single source of truth for conversation state
✅ Agent has working memory for complex tasks
✅ No state conflicts (different purposes)
✅ Consistent conversation history
✅ Clear separation of concerns
✅ LangGraph nodes control conversation state flow
