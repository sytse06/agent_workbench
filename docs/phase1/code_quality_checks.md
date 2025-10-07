Running code quality checks...
🧹 Checking code formatting...
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/__init__.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/api/routes/health.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/main.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/models/config.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/api/database.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/api/exceptions.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/api/routes/agent_configs.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/conftest.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/api/routes/conversations.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/unit/api/test_health.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/api/routes/messages.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/models/schemas.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/integration/test_database_operations.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/src/agent_workbench/models/database.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/unit/api/test_conversations.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/unit/models/test_database.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/unit/api/test_messages.py
would reformat /Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/tests/unit/api/test_agent_configs.py

Oh no! 💥 💔 💥
18 files would be reformatted, 4 files would be left unchanged.
🔍 Checking code style...
warning: The top-level linter settings are deprecated in favour of their counterparts in the `lint` section. Please update the following options in `pyproject.toml`:
  - 'select' -> 'lint.select'
I001 [*] Import block is un-sorted or un-formatted
 --> src/agent_workbench/__main__.py:1:1
  |
1 | / from .main import app
2 | | import uvicorn
  | |______________^
3 |
4 |   if __name__ == "__main__":
  |
help: Organize imports

I001 [*] Import block is un-sorted or un-formatted
  --> src/agent_workbench/api/database.py:3:1
   |
 1 |   """Database session management for Agent Workbench API."""
 2 |
 3 | / from typing import AsyncGenerator, Optional
 4 | | import asyncio
 5 | |
 6 | | from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
 7 | | from sqlalchemy.orm import sessionmaker
 8 | | from sqlalchemy.exc import SQLAlchemyError
 9 | | from sqlalchemy.engine import URL
10 | |
11 | | from agent_workbench.models.database import Base
12 | | from agent_workbench.models.config import DatabaseConfig
   | |________________________________________________________^
   |
help: Organize imports

F401 [*] `asyncio` imported but unused
 --> src/agent_workbench/api/database.py:4:8
  |
3 | from typing import AsyncGenerator, Optional
4 | import asyncio
  |        ^^^^^^^
5 |
6 | from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
  |
help: Remove unused import: `asyncio`

F401 [*] `sqlalchemy.engine.URL` imported but unused
  --> src/agent_workbench/api/database.py:9:31
   |
 7 | from sqlalchemy.orm import sessionmaker
 8 | from sqlalchemy.exc import SQLAlchemyError
 9 | from sqlalchemy.engine import URL
   |                               ^^^
10 |
11 | from agent_workbench.models.database import Base
   |
help: Remove unused import: `sqlalchemy.engine.URL`

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:17:1
   |
15 | class DatabaseManager:
16 |     """Manages database connections and sessions."""
17 |     
   | ^^^^
18 |     def __init__(self, config: DatabaseConfig):
19 |         self.config = config
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:22:1
   |
20 |         self.engine = None
21 |         self.session_factory = None
22 |         
   | ^^^^^^^^
23 |     async def initialize(self) -> None:
24 |         """Initialize the database engine and session factory."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:27:1
   |
25 |         if self.engine is not None:
26 |             return
27 |             
   | ^^^^^^^^^^^^
28 |         # Create async engine
29 |         # SQLite doesn't support pool_size, max_overflow, pool_timeout
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:45:1
   |
43 |                 pool_recycle=self.config.pool_recycle,
44 |             )
45 |         
   | ^^^^^^^^
46 |         # Create session factory
47 |         self.session_factory = sessionmaker(
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/database.py:48:25
   |
46 |         # Create session factory
47 |         self.session_factory = sessionmaker(
48 |             self.engine, 
   |                         ^
49 |             class_=AsyncSession, 
50 |             expire_on_commit=False
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/database.py:49:33
   |
47 |         self.session_factory = sessionmaker(
48 |             self.engine, 
49 |             class_=AsyncSession, 
   |                                 ^
50 |             expire_on_commit=False
51 |         )
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:52:1
   |
50 |             expire_on_commit=False
51 |         )
52 |         
   | ^^^^^^^^
53 |     async def close(self) -> None:
54 |         """Close the database engine."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:59:1
   |
57 |             self.engine = None
58 |             self.session_factory = None
59 |     
   | ^^^^
60 |     async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
61 |         """Get a database session dependency."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:64:1
   |
62 |         if self.session_factory is None:
63 |             await self.initialize()
64 |             
   | ^^^^^^^^^^^^
65 |         async with self.session_factory() as session:
66 |             try:
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:73:1
   |
71 |             finally:
72 |                 await session.close()
73 |     
   | ^^^^
74 |     async def create_tables(self) -> None:
75 |         """Create all tables defined in the models."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:78:1
   |
76 |         if self.engine is None:
77 |             await self.initialize()
78 |             
   | ^^^^^^^^^^^^
79 |         async with self.engine.begin() as conn:
80 |             await conn.run_sync(Base.metadata.create_all)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:81:1
   |
79 |         async with self.engine.begin() as conn:
80 |             await conn.run_sync(Base.metadata.create_all)
81 |     
   | ^^^^
82 |     async def drop_tables(self) -> None:
83 |         """Drop all tables (for testing)."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:86:1
   |
84 |         if self.engine is None:
85 |             await self.initialize()
86 |             
   | ^^^^^^^^^^^^
87 |         async with self.engine.begin() as conn:
88 |             await conn.run_sync(Base.metadata.drop_all)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:89:1
   |
87 |         async with self.engine.begin() as conn:
88 |             await conn.run_sync(Base.metadata.drop_all)
89 |     
   | ^^^^
90 |     async def check_database_connection(self) -> bool:
91 |         """Check if database is accessible."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/database.py:95:1
   |
93 |         if self.engine is None and self.session_factory is None:
94 |             return False
95 |             
   | ^^^^^^^^^^^^
96 |         try:
97 |             if self.engine is None:
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/database.py:99:1
    |
 97 |             if self.engine is None:
 98 |                 await self.initialize()
 99 |                 
    | ^^^^^^^^^^^^^^^^
100 |             from sqlalchemy import text
101 |             async with self.engine.connect() as conn:
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/database.py:152:1
    |
150 |         if db_manager.engine is None:
151 |             return False
152 |             
    | ^^^^^^^^^^^^
153 |         from sqlalchemy import text
154 |         async with db_manager.engine.connect() as conn:
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
 --> src/agent_workbench/api/exceptions.py:3:1
  |
1 |   """Custom API exceptions for Agent Workbench."""
2 |
3 | / from typing import Optional
4 | | from fastapi import HTTPException, status
  | |_________________________________________^
  |
help: Organize imports

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:9:1
   |
 7 | class DatabaseError(HTTPException):
 8 |     """Base exception for database-related errors."""
 9 |     
   | ^^^^
10 |     def __init__(
11 |         self, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/exceptions.py:11:14
   |
10 |     def __init__(
11 |         self, 
   |              ^
12 |         detail: str = "Database operation failed",
13 |         error_code: Optional[str] = None
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:26:1
   |
24 | class NotFoundError(HTTPException):
25 |     """Exception for when a resource is not found."""
26 |     
   | ^^^^
27 |     def __init__(
28 |         self, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/exceptions.py:28:14
   |
27 |     def __init__(
28 |         self, 
   |              ^
29 |         resource: str = "Resource",
30 |         resource_id: Optional[str] = None,
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:36:1
   |
34 |         if resource_id:
35 |             detail = f"{resource} with id '{resource_id}' not found"
36 |             
   | ^^^^^^^^^^^^
37 |         super().__init__(
38 |             status_code=status.HTTP_404_NOT_FOUND,
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:48:1
   |
46 | class ValidationError(HTTPException):
47 |     """Exception for validation errors."""
48 |     
   | ^^^^
49 |     def __init__(
50 |         self, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/exceptions.py:50:14
   |
49 |     def __init__(
50 |         self, 
   |              ^
51 |         detail: str = "Validation failed",
52 |         error_code: Optional[str] = None
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:65:1
   |
63 | class ConflictError(HTTPException):
64 |     """Exception for conflicts (e.g., duplicate resources)."""
65 |     
   | ^^^^
66 |     def __init__(
67 |         self, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/exceptions.py:67:14
   |
66 |     def __init__(
67 |         self, 
   |              ^
68 |         detail: str = "Resource conflict",
69 |         error_code: Optional[str] = None
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:83:1
   |
81 | class ConversationNotFoundError(NotFoundError):
82 |     """Exception for when a conversation is not found."""
83 |     
   | ^^^^
84 |     def __init__(self, conversation_id: Optional[str] = None):
85 |         super().__init__(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/exceptions.py:94:1
   |
92 | class MessageNotFoundError(NotFoundError):
93 |     """Exception for when a message is not found."""
94 |     
   | ^^^^
95 |     def __init__(self, message_id: Optional[str] = None):
96 |         super().__init__(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/exceptions.py:105:1
    |
103 | class AgentConfigNotFoundError(NotFoundError):
104 |     """Exception for when an agent configuration is not found."""
105 |     
    | ^^^^
106 |     def __init__(self, config_id: Optional[str] = None):
107 |         super().__init__(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/exceptions.py:116:1
    |
114 | class AgentConfigConflictError(ConflictError):
115 |     """Exception for when an agent configuration conflicts."""
116 |     
    | ^^^^
117 |     def __init__(self, detail: str = "Agent configuration already exists"):
118 |         super().__init__(
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> src/agent_workbench/api/routes/agent_configs.py:3:1
   |
 1 |   """Agent configuration API routes for Agent Workbench."""
 2 |
 3 | / from typing import List
 4 | | from uuid import UUID
 5 | |
 6 | | from fastapi import APIRouter, Depends, status
 7 | | from sqlalchemy.ext.asyncio import AsyncSession
 8 | |
 9 | | from agent_workbench.models.database import AgentConfigModel
10 | | from agent_workbench.models.schemas import (
11 | |     AgentConfigCreate, 
12 | |     AgentConfigUpdate, 
13 | |     AgentConfigResponse
14 | | )
15 | | from agent_workbench.api.database import get_session
16 | | from agent_workbench.api.exceptions import (
17 | |     AgentConfigNotFoundError, 
18 | |     AgentConfigConflictError
19 | | )
   | |_^
20 |
21 |   router = APIRouter(
   |
help: Organize imports

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:11:23
   |
 9 | from agent_workbench.models.database import AgentConfigModel
10 | from agent_workbench.models.schemas import (
11 |     AgentConfigCreate, 
   |                       ^
12 |     AgentConfigUpdate, 
13 |     AgentConfigResponse
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:12:23
   |
10 | from agent_workbench.models.schemas import (
11 |     AgentConfigCreate, 
12 |     AgentConfigUpdate, 
   |                       ^
13 |     AgentConfigResponse
14 | )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:17:30
   |
15 | from agent_workbench.api.database import get_session
16 | from agent_workbench.api.exceptions import (
17 |     AgentConfigNotFoundError, 
   |                              ^
18 |     AgentConfigConflictError
19 | )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:28:9
   |
27 | @router.post(
28 |     "/", 
   |         ^
29 |     response_model=AgentConfigResponse,
30 |     status_code=status.HTTP_201_CREATED,
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:35:32
   |
33 | )
34 | async def create_agent_config(
35 |     request: AgentConfigCreate, 
   |                                ^
36 |     session: AsyncSession = Depends(get_session)
37 | ) -> AgentConfigResponse:
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:49:1
   |
47 |             f"Agent configuration with name '{request.name}' already exists"
48 |         )
49 |     
   | ^^^^
50 |     agent_config = await AgentConfigModel.create(
51 |         session, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:51:17
   |
50 |     agent_config = await AgentConfigModel.create(
51 |         session, 
   |                 ^
52 |         **request.model_dump()
53 |     )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:58:20
   |
57 | @router.get(
58 |     "/{config_id}", 
   |                    ^
59 |     response_model=AgentConfigResponse,
60 |     summary="Get agent configuration",
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:64:21
   |
62 | )
63 | async def get_agent_config(
64 |     config_id: UUID, 
   |                     ^
65 |     session: AsyncSession = Depends(get_session)
66 | ) -> AgentConfigResponse:
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:75:9
   |
74 | @router.get(
75 |     "/", 
   |         ^
76 |     response_model=List[AgentConfigResponse],
77 |     summary="List agent configurations",
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:86:51
   |
84 |     agent_configs = await AgentConfigModel.get_all(session)
85 |     return [
86 |         AgentConfigResponse.model_validate(config) 
   |                                                   ^
87 |         for config in agent_configs
88 |     ]
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/agent_configs.py:92:20
   |
91 | @router.put(
92 |     "/{config_id}", 
   |                    ^
93 |     response_model=AgentConfigResponse,
94 |     summary="Update agent configuration",
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/routes/agent_configs.py:106:1
    |
104 |     if agent_config is None:
105 |         raise AgentConfigNotFoundError(str(config_id))
106 |     
    | ^^^^
107 |     # Check if new name conflicts with existing config
108 |     if request.name and request.name != agent_config.name:
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/routes/agent_configs.py:119:1
    |
117 |                 f"Agent configuration with name '{request.name}' already exists"
118 |             )
119 |     
    | ^^^^
120 |     update_data = request.model_dump(exclude_unset=True)
121 |     updated_config = await agent_config.update(session, **update_data)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/routes/agent_configs.py:139:1
    |
137 |     if agent_config is None:
138 |         raise AgentConfigNotFoundError(str(config_id))
139 |     
    | ^^^^
140 |     await agent_config.delete(session)
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> src/agent_workbench/api/routes/conversations.py:3:1
   |
 1 |   """Conversation API routes for Agent Workbench."""
 2 |
 3 | / from typing import List, Optional
 4 | | from uuid import UUID
 5 | |
 6 | | from fastapi import APIRouter, Depends, status
 7 | | from sqlalchemy.ext.asyncio import AsyncSession
 8 | |
 9 | | from agent_workbench.models.database import ConversationModel
10 | | from agent_workbench.models.schemas import (
11 | |     ConversationCreate, 
12 | |     ConversationUpdate, 
13 | |     ConversationResponse
14 | | )
15 | | from agent_workbench.api.database import get_session
16 | | from agent_workbench.api.exceptions import ConversationNotFoundError
   | |____________________________________________________________________^
17 |
18 |   router = APIRouter(
   |
help: Organize imports

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:11:24
   |
 9 | from agent_workbench.models.database import ConversationModel
10 | from agent_workbench.models.schemas import (
11 |     ConversationCreate, 
   |                        ^
12 |     ConversationUpdate, 
13 |     ConversationResponse
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:12:24
   |
10 | from agent_workbench.models.schemas import (
11 |     ConversationCreate, 
12 |     ConversationUpdate, 
   |                        ^
13 |     ConversationResponse
14 | )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:25:9
   |
24 | @router.post(
25 |     "/", 
   |         ^
26 |     response_model=ConversationResponse,
27 |     status_code=status.HTTP_201_CREATED,
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:32:33
   |
30 | )
31 | async def create_conversation(
32 |     request: ConversationCreate, 
   |                                 ^
33 |     session: AsyncSession = Depends(get_session)
34 | ) -> ConversationResponse:
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:41:26
   |
40 | @router.get(
41 |     "/{conversation_id}", 
   |                          ^
42 |     response_model=ConversationResponse,
43 |     summary="Get conversation",
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:47:27
   |
45 | )
46 | async def get_conversation(
47 |     conversation_id: UUID, 
   |                           ^
48 |     session: AsyncSession = Depends(get_session)
49 | ) -> ConversationResponse:
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:58:9
   |
57 | @router.get(
58 |     "/", 
   |         ^
59 |     response_model=List[ConversationResponse],
60 |     summary="List conversations",
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/routes/conversations.py:73:1
   |
71 |         result = await session.execute(ConversationModel.__table__.select())
72 |         conversations = list(result.scalars().all())
73 |     
   | ^^^^
74 |     return [
75 |         ConversationResponse.model_validate(conv) 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:75:50
   |
74 |     return [
75 |         ConversationResponse.model_validate(conv) 
   |                                                  ^
76 |         for conv in conversations
77 |     ]
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:81:26
   |
80 | @router.put(
81 |     "/{conversation_id}", 
   |                          ^
82 |     response_model=ConversationResponse,
83 |     summary="Update conversation",
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/routes/conversations.py:95:1
   |
93 |     if conversation is None:
94 |         raise ConversationNotFoundError(str(conversation_id))
95 |     
   | ^^^^
96 |     updated_conversation = await conversation.update(
97 |         session, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/conversations.py:97:17
   |
96 |     updated_conversation = await conversation.update(
97 |         session, 
   |                 ^
98 |         **request.model_dump(exclude_unset=True)
99 |     )
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/routes/conversations.py:117:1
    |
115 |     if conversation is None:
116 |         raise ConversationNotFoundError(str(conversation_id))
117 |     
    | ^^^^
118 |     await conversation.delete(session)
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> src/agent_workbench/api/routes/health.py:3:1
   |
 1 |   """Health check API routes for Agent Workbench."""
 2 |
 3 | / from datetime import datetime
 4 | |
 5 | | from fastapi import APIRouter, Depends
 6 | | from sqlalchemy.ext.asyncio import AsyncSession
 7 | |
 8 | | from agent_workbench.models.schemas import HealthCheckResponse
 9 | | from agent_workbench.api.database import get_session, check_database_connection
   | |_______________________________________________________________________________^
10 |
11 |   router = APIRouter(
   |
help: Organize imports

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/health.py:18:9
   |
17 | @router.get(
18 |     "/", 
   |         ^
19 |     response_model=HealthCheckResponse,
20 |     summary="Health check",
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/routes/health.py:29:1
   |
27 |     # Check database connectivity
28 |     database_connected = await check_database_connection()
29 |     
   | ^^^^
30 |     return HealthCheckResponse(
31 |         status="healthy" if database_connected else "unhealthy",
   |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> src/agent_workbench/api/routes/messages.py:3:1
   |
 1 |   """Message API routes for Agent Workbench."""
 2 |
 3 | / from typing import List
 4 | | from uuid import UUID
 5 | |
 6 | | from fastapi import APIRouter, Depends, status
 7 | | from sqlalchemy.ext.asyncio import AsyncSession
 8 | |
 9 | | from agent_workbench.models.database import MessageModel, ConversationModel
10 | | from agent_workbench.models.schemas import (
11 | |     MessageCreate, 
12 | |     MessageUpdate, 
13 | |     MessageResponse
14 | | )
15 | | from agent_workbench.api.database import get_session
16 | | from agent_workbench.api.exceptions import (
17 | |     MessageNotFoundError, 
18 | |     ConversationNotFoundError
19 | | )
   | |_^
20 |
21 |   router = APIRouter(
   |
help: Organize imports

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:11:19
   |
 9 | from agent_workbench.models.database import MessageModel, ConversationModel
10 | from agent_workbench.models.schemas import (
11 |     MessageCreate, 
   |                   ^
12 |     MessageUpdate, 
13 |     MessageResponse
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:12:19
   |
10 | from agent_workbench.models.schemas import (
11 |     MessageCreate, 
12 |     MessageUpdate, 
   |                   ^
13 |     MessageResponse
14 | )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:17:26
   |
15 | from agent_workbench.api.database import get_session
16 | from agent_workbench.api.exceptions import (
17 |     MessageNotFoundError, 
   |                          ^
18 |     ConversationNotFoundError
19 | )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:28:9
   |
27 | @router.post(
28 |     "/", 
   |         ^
29 |     response_model=MessageResponse,
30 |     status_code=status.HTTP_201_CREATED,
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:35:28
   |
33 | )
34 | async def create_message(
35 |     request: MessageCreate, 
   |                            ^
36 |     session: AsyncSession = Depends(get_session)
37 | ) -> MessageResponse:
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:41:17
   |
39 |     # Verify conversation exists
40 |     conversation = await ConversationModel.get_by_id(
41 |         session, 
   |                 ^
42 |         request.conversation_id
43 |     )
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/routes/messages.py:46:1
   |
44 |     if conversation is None:
45 |         raise ConversationNotFoundError(str(request.conversation_id))
46 |     
   | ^^^^
47 |     message = await MessageModel.create(
48 |         session, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:48:17
   |
47 |     message = await MessageModel.create(
48 |         session, 
   |                 ^
49 |         **request.model_dump(by_alias=True)
50 |     )
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:55:21
   |
54 | @router.get(
55 |     "/{message_id}", 
   |                     ^
56 |     response_model=MessageResponse,
57 |     summary="Get message",
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:61:22
   |
59 | )
60 | async def get_message(
61 |     message_id: UUID, 
   |                      ^
62 |     session: AsyncSession = Depends(get_session)
63 | ) -> MessageResponse:
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:72:9
   |
71 | @router.get(
72 |     "/", 
   |         ^
73 |     response_model=List[MessageResponse],
74 |     summary="List messages",
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/api/routes/messages.py:86:1
   |
84 |     if conversation is None:
85 |         raise ConversationNotFoundError(str(conversation_id))
86 |     
   | ^^^^
87 |     messages = await MessageModel.get_by_conversation(session, conversation_id)
88 |     return [
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:89:44
   |
87 |     messages = await MessageModel.get_by_conversation(session, conversation_id)
88 |     return [
89 |         MessageResponse.model_validate(msg) 
   |                                            ^
90 |         for msg in messages
91 |     ]
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/api/routes/messages.py:95:21
   |
94 | @router.put(
95 |     "/{message_id}", 
   |                     ^
96 |     response_model=MessageResponse,
97 |     summary="Update message",
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/routes/messages.py:109:1
    |
107 |     if message is None:
108 |         raise MessageNotFoundError(str(message_id))
109 |     
    | ^^^^
110 |     update_data = request.model_dump(exclude_unset=True, by_alias=True)
111 |     updated_message = await message.update(session, **update_data)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/api/routes/messages.py:129:1
    |
127 |     if message is None:
128 |         raise MessageNotFoundError(str(message_id))
129 |     
    | ^^^^
130 |     await message.delete(session)
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
 --> src/agent_workbench/models/config.py:3:1
  |
1 |   """Database configuration for Agent Workbench."""
2 |
3 | / from typing import Optional
4 | | from pydantic import BaseModel, Field
  | |_____________________________________^
  |
help: Organize imports

F401 [*] `typing.Optional` imported but unused
 --> src/agent_workbench/models/config.py:3:20
  |
1 | """Database configuration for Agent Workbench."""
2 |
3 | from typing import Optional
  |                    ^^^^^^^^
4 | from pydantic import BaseModel, Field
  |
help: Remove unused import: `typing.Optional`

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:9:1
   |
 7 | class DatabaseConfig(BaseModel):
 8 |     """Configuration for database connection."""
 9 |     
   | ^^^^
10 |     # Database URL (e.g., "postgresql+asyncpg://user:pass@localhost/db")
11 |     database_url: str = Field(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:15:1
   |
13 |         description="Database connection URL"
14 |     )
15 |     
   | ^^^^
16 |     # Connection pool settings
17 |     pool_size: int = Field(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:21:1
   |
19 |         description="Connection pool size"
20 |     )
21 |     
   | ^^^^
22 |     max_overflow: int = Field(
23 |         default=20,
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:26:1
   |
24 |         description="Maximum overflow connections"
25 |     )
26 |     
   | ^^^^
27 |     pool_timeout: int = Field(
28 |         default=30,
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:31:1
   |
29 |         description="Pool timeout in seconds"
30 |     )
31 |     
   | ^^^^
32 |     pool_recycle: int = Field(
33 |         default=3600,
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:36:1
   |
34 |         description="Pool recycle time in seconds"
35 |     )
36 |     
   | ^^^^
37 |     # Echo SQL statements (for debugging)
38 |     echo_sql: bool = Field(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/config.py:42:1
   |
40 |         description="Echo SQL statements to stdout"
41 |     )
42 |     
   | ^^^^
43 |     # Future: Add more database-specific configurations
   |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> src/agent_workbench/models/database.py:3:1
   |
 1 |   """SQLAlchemy async models for Agent Workbench database."""
 2 |
 3 | / from typing import List, Optional
 4 | | from uuid import UUID, uuid4
 5 | |
 6 | | from sqlalchemy import (
 7 | |     select, DateTime, String, Text, ForeignKey, 
 8 | |     CheckConstraint, Index, JSON
 9 | | )
10 | | from sqlalchemy.ext.asyncio import AsyncSession
11 | | from sqlalchemy.ext.declarative import declarative_base
12 | | from sqlalchemy.orm import relationship, mapped_column
13 | | from sqlalchemy.sql import func
14 | | from sqlalchemy.dialects.postgresql import UUID as PG_UUID
   | |__________________________________________________________^
15 |
16 |   Base = declarative_base()
   |
help: Organize imports

F401 [*] `sqlalchemy.select` imported but unused
 --> src/agent_workbench/models/database.py:7:5
  |
6 | from sqlalchemy import (
7 |     select, DateTime, String, Text, ForeignKey, 
  |     ^^^^^^
8 |     CheckConstraint, Index, JSON
9 | )
  |
help: Remove unused import: `sqlalchemy.select`

W291 [*] Trailing whitespace
 --> src/agent_workbench/models/database.py:7:48
  |
6 | from sqlalchemy import (
7 |     select, DateTime, String, Text, ForeignKey, 
  |                                                ^
8 |     CheckConstraint, Index, JSON
9 | )
  |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:30:1
   |
28 |     """SQLAlchemy model for conversations table."""
29 |     __tablename__ = "conversations"
30 |     
   | ^^^^
31 |     id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
32 |     user_id = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # Future multi-user support
   |
help: Remove whitespace from blank line

E501 Line too long (94 > 88)
  --> src/agent_workbench/models/database.py:32:89
   |
31 |     id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
32 |     user_id = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # Future multi-user support
   |                                                                                         ^^^^^^
33 |     title = mapped_column(String(255), nullable=True)
   |

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:34:1
   |
32 |     user_id = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # Future multi-user support
33 |     title = mapped_column(String(255), nullable=True)
34 |     
   | ^^^^
35 |     # Relationships
36 |     messages = relationship(
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:37:24
   |
35 |     # Relationships
36 |     messages = relationship(
37 |         "MessageModel", 
   |                        ^
38 |         back_populates="conversation", 
39 |         cascade="all, delete-orphan",
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:38:39
   |
36 |     messages = relationship(
37 |         "MessageModel", 
38 |         back_populates="conversation", 
   |                                       ^
39 |         cascade="all, delete-orphan",
40 |         lazy="select"
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:42:1
   |
40 |         lazy="select"
41 |     )
42 |     
   | ^^^^
43 |     __table_args__ = (
44 |         Index("idx_conversations_user_id", "user_id"),
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:46:1
   |
44 |         Index("idx_conversations_user_id", "user_id"),
45 |     )
46 |     
   | ^^^^
47 |     @classmethod
48 |     async def create(
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:49:13
   |
47 |     @classmethod
48 |     async def create(
49 |         cls, 
   |             ^
50 |         session: AsyncSession, 
51 |         **kwargs
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:50:31
   |
48 |     async def create(
49 |         cls, 
50 |         session: AsyncSession, 
   |                               ^
51 |         **kwargs
52 |     ) -> "ConversationModel":
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:59:1
   |
57 |         await session.refresh(conversation)
58 |         return conversation
59 |     
   | ^^^^
60 |     @classmethod
61 |     async def get_by_id(
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:62:13
   |
60 |     @classmethod
61 |     async def get_by_id(
62 |         cls, 
   |             ^
63 |         session: AsyncSession, 
64 |         id: UUID
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:63:31
   |
61 |     async def get_by_id(
62 |         cls, 
63 |         session: AsyncSession, 
   |                               ^
64 |         id: UUID
65 |     ) -> Optional["ConversationModel"]:
   |
help: Remove trailing whitespace

F811 [*] Redefinition of unused `select` from line 7
  --> src/agent_workbench/models/database.py:67:32
   |
65 |     ) -> Optional["ConversationModel"]:
66 |         """Get conversation by ID."""
67 |         from sqlalchemy import select
   |                                ^^^^^^ `select` redefined here
68 |         result = await session.execute(
69 |             select(cls).where(cls.id == id)
   |
  ::: src/agent_workbench/models/database.py:7:5
   |
 6 | from sqlalchemy import (
 7 |     select, DateTime, String, Text, ForeignKey, 
   |     ------ previous definition of `select` here
 8 |     CheckConstraint, Index, JSON
 9 | )
   |
help: Remove definition: `select`

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:72:1
   |
70 |         )
71 |         return result.scalar_one_or_none()
72 |     
   | ^^^^
73 |     @classmethod
74 |     async def get_by_user(
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:75:13
   |
73 |     @classmethod
74 |     async def get_by_user(
75 |         cls, 
   |             ^
76 |         session: AsyncSession, 
77 |         user_id: UUID
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:76:31
   |
74 |     async def get_by_user(
75 |         cls, 
76 |         session: AsyncSession, 
   |                               ^
77 |         user_id: UUID
78 |     ) -> List["ConversationModel"]:
   |
help: Remove trailing whitespace

F811 [*] Redefinition of unused `select` from line 7
  --> src/agent_workbench/models/database.py:80:32
   |
78 |     ) -> List["ConversationModel"]:
79 |         """Get conversations by user ID."""
80 |         from sqlalchemy import select
   |                                ^^^^^^ `select` redefined here
81 |         result = await session.execute(
82 |             select(cls).where(cls.user_id == user_id)
   |
  ::: src/agent_workbench/models/database.py:7:5
   |
 6 | from sqlalchemy import (
 7 |     select, DateTime, String, Text, ForeignKey, 
   |     ------ previous definition of `select` here
 8 |     CheckConstraint, Index, JSON
 9 | )
   |
help: Remove definition: `select`

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:85:1
   |
83 |         )
84 |         return list(result.scalars().all())
85 |     
   | ^^^^
86 |     async def update(
87 |         self, 
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:87:14
   |
86 |     async def update(
87 |         self, 
   |              ^
88 |         session: AsyncSession, 
89 |         **kwargs
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> src/agent_workbench/models/database.py:88:31
   |
86 |     async def update(
87 |         self, 
88 |         session: AsyncSession, 
   |                               ^
89 |         **kwargs
90 |     ) -> "ConversationModel":
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> src/agent_workbench/models/database.py:97:1
   |
95 |         await session.refresh(self)
96 |         return self
97 |     
   | ^^^^
98 |     async def delete(self, session: AsyncSession) -> None:
99 |         """Delete conversation."""
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:107:1
    |
105 |     """SQLAlchemy model for messages table."""
106 |     __tablename__ = "messages"
107 |     
    | ^^^^
108 |     id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
109 |     conversation_id = mapped_column(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:110:31
    |
108 |     id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
109 |     conversation_id = mapped_column(
110 |         PG_UUID(as_uuid=True), 
    |                               ^
111 |         ForeignKey("conversations.id", ondelete="CASCADE"), 
112 |         nullable=False
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:111:60
    |
109 |     conversation_id = mapped_column(
110 |         PG_UUID(as_uuid=True), 
111 |         ForeignKey("conversations.id", ondelete="CASCADE"), 
    |                                                            ^
112 |         nullable=False
113 |     )
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:115:20
    |
113 |     )
114 |     role = mapped_column(
115 |         String(20), 
    |                    ^
116 |         CheckConstraint("role IN ('user', 'assistant', 'tool', 'system')"),
117 |         nullable=False
    |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:122:1
    |
120 |     metadata_ = mapped_column("metadata", JSON, nullable=True)
121 |     created_at = mapped_column(DateTime, default=func.now(), nullable=False)
122 |     
    | ^^^^
123 |     # Relationships
124 |     conversation = relationship("ConversationModel", back_populates="messages")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:125:1
    |
123 |     # Relationships
124 |     conversation = relationship("ConversationModel", back_populates="messages")
125 |     
    | ^^^^
126 |     __table_args__ = (
127 |         Index("idx_messages_conversation_id", "conversation_id"),
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:130:1
    |
128 |         Index("idx_messages_created_at", "created_at"),
129 |     )
130 |     
    | ^^^^
131 |     @classmethod
132 |     async def create(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:133:13
    |
131 |     @classmethod
132 |     async def create(
133 |         cls, 
    |             ^
134 |         session: AsyncSession, 
135 |         **kwargs
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:134:31
    |
132 |     async def create(
133 |         cls, 
134 |         session: AsyncSession, 
    |                               ^
135 |         **kwargs
136 |     ) -> "MessageModel":
    |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:143:1
    |
141 |         await session.refresh(message)
142 |         return message
143 |     
    | ^^^^
144 |     @classmethod
145 |     async def get_by_conversation(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:146:13
    |
144 |     @classmethod
145 |     async def get_by_conversation(
146 |         cls, 
    |             ^
147 |         session: AsyncSession, 
148 |         conversation_id: UUID
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:147:31
    |
145 |     async def get_by_conversation(
146 |         cls, 
147 |         session: AsyncSession, 
    |                               ^
148 |         conversation_id: UUID
149 |     ) -> List["MessageModel"]:
    |
help: Remove trailing whitespace

F811 [*] Redefinition of unused `select` from line 7
   --> src/agent_workbench/models/database.py:151:32
    |
149 |     ) -> List["MessageModel"]:
150 |         """Get messages by conversation ID."""
151 |         from sqlalchemy import select
    |                                ^^^^^^ `select` redefined here
152 |         result = await session.execute(
153 |             select(cls)
    |
   ::: src/agent_workbench/models/database.py:7:5
    |
  6 | from sqlalchemy import (
  7 |     select, DateTime, String, Text, ForeignKey, 
    |     ------ previous definition of `select` here
  8 |     CheckConstraint, Index, JSON
  9 | )
    |
help: Remove definition: `select`

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:158:1
    |
156 |         )
157 |         return list(result.scalars().all())
158 |     
    | ^^^^
159 |     @classmethod
160 |     async def get_by_id(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:161:13
    |
159 |     @classmethod
160 |     async def get_by_id(
161 |         cls, 
    |             ^
162 |         session: AsyncSession, 
163 |         id: UUID
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:162:31
    |
160 |     async def get_by_id(
161 |         cls, 
162 |         session: AsyncSession, 
    |                               ^
163 |         id: UUID
164 |     ) -> Optional["MessageModel"]:
    |
help: Remove trailing whitespace

F811 [*] Redefinition of unused `select` from line 7
   --> src/agent_workbench/models/database.py:166:32
    |
164 |     ) -> Optional["MessageModel"]:
165 |         """Get message by ID."""
166 |         from sqlalchemy import select
    |                                ^^^^^^ `select` redefined here
167 |         result = await session.execute(
168 |             select(cls).where(cls.id == id)
    |
   ::: src/agent_workbench/models/database.py:7:5
    |
  6 | from sqlalchemy import (
  7 |     select, DateTime, String, Text, ForeignKey, 
    |     ------ previous definition of `select` here
  8 |     CheckConstraint, Index, JSON
  9 | )
    |
help: Remove definition: `select`

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:171:1
    |
169 |         )
170 |         return result.scalar_one_or_none()
171 |     
    | ^^^^
172 |     async def update(
173 |         self, 
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:173:14
    |
172 |     async def update(
173 |         self, 
    |              ^
174 |         session: AsyncSession, 
175 |         **kwargs
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:174:31
    |
172 |     async def update(
173 |         self, 
174 |         session: AsyncSession, 
    |                               ^
175 |         **kwargs
176 |     ) -> "MessageModel":
    |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:183:1
    |
181 |         await session.refresh(self)
182 |         return self
183 |     
    | ^^^^
184 |     async def delete(self, session: AsyncSession) -> None:
185 |         """Delete message."""
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:193:1
    |
191 |     """SQLAlchemy model for agent configurations table."""
192 |     __tablename__ = "agent_configs"
193 |     
    | ^^^^
194 |     id = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
195 |     name = mapped_column(String(255), nullable=False)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:198:1
    |
196 |     description = mapped_column(Text, nullable=True)
197 |     config = mapped_column(JSON, nullable=False)
198 |     
    | ^^^^
199 |     __table_args__ = (
200 |         Index("idx_agent_configs_name", "name"),
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:202:1
    |
200 |         Index("idx_agent_configs_name", "name"),
201 |     )
202 |     
    | ^^^^
203 |     @classmethod
204 |     async def create(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:205:13
    |
203 |     @classmethod
204 |     async def create(
205 |         cls, 
    |             ^
206 |         session: AsyncSession, 
207 |         **kwargs
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:206:31
    |
204 |     async def create(
205 |         cls, 
206 |         session: AsyncSession, 
    |                               ^
207 |         **kwargs
208 |     ) -> "AgentConfigModel":
    |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:215:1
    |
213 |         await session.refresh(agent_config)
214 |         return agent_config
215 |     
    | ^^^^
216 |     @classmethod
217 |     async def get_by_id(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:218:13
    |
216 |     @classmethod
217 |     async def get_by_id(
218 |         cls, 
    |             ^
219 |         session: AsyncSession, 
220 |         id: UUID
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:219:31
    |
217 |     async def get_by_id(
218 |         cls, 
219 |         session: AsyncSession, 
    |                               ^
220 |         id: UUID
221 |     ) -> Optional["AgentConfigModel"]:
    |
help: Remove trailing whitespace

F811 [*] Redefinition of unused `select` from line 7
   --> src/agent_workbench/models/database.py:223:32
    |
221 |     ) -> Optional["AgentConfigModel"]:
222 |         """Get agent configuration by ID."""
223 |         from sqlalchemy import select
    |                                ^^^^^^ `select` redefined here
224 |         result = await session.execute(
225 |             select(cls).where(cls.id == id)
    |
   ::: src/agent_workbench/models/database.py:7:5
    |
  6 | from sqlalchemy import (
  7 |     select, DateTime, String, Text, ForeignKey, 
    |     ------ previous definition of `select` here
  8 |     CheckConstraint, Index, JSON
  9 | )
    |
help: Remove definition: `select`

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:228:1
    |
226 |         )
227 |         return result.scalar_one_or_none()
228 |     
    | ^^^^
229 |     @classmethod
230 |     async def get_all(
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:231:13
    |
229 |     @classmethod
230 |     async def get_all(
231 |         cls, 
    |             ^
232 |         session: AsyncSession
233 |     ) -> List["AgentConfigModel"]:
    |
help: Remove trailing whitespace

F811 [*] Redefinition of unused `select` from line 7
   --> src/agent_workbench/models/database.py:235:32
    |
233 |     ) -> List["AgentConfigModel"]:
234 |         """Get all agent configurations."""
235 |         from sqlalchemy import select
    |                                ^^^^^^ `select` redefined here
236 |         result = await session.execute(select(cls))
237 |         return list(result.scalars().all())
    |
   ::: src/agent_workbench/models/database.py:7:5
    |
  6 | from sqlalchemy import (
  7 |     select, DateTime, String, Text, ForeignKey, 
    |     ------ previous definition of `select` here
  8 |     CheckConstraint, Index, JSON
  9 | )
    |
help: Remove definition: `select`

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:238:1
    |
236 |         result = await session.execute(select(cls))
237 |         return list(result.scalars().all())
238 |     
    | ^^^^
239 |     async def update(
240 |         self, 
    |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:240:14
    |
239 |     async def update(
240 |         self, 
    |              ^
241 |         session: AsyncSession, 
242 |         **kwargs
    |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
   --> src/agent_workbench/models/database.py:241:31
    |
239 |     async def update(
240 |         self, 
241 |         session: AsyncSession, 
    |                               ^
242 |         **kwargs
243 |     ) -> "AgentConfigModel":
    |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
   --> src/agent_workbench/models/database.py:250:1
    |
248 |         await session.refresh(self)
249 |         return self
250 |     
    | ^^^^
251 |     async def delete(self, session: AsyncSession) -> None:
252 |         """Delete agent configuration."""
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
 --> src/agent_workbench/models/schemas.py:3:1
  |
1 |   """Pydantic schemas for Agent Workbench API."""
2 |
3 | / from typing import List, Optional, Dict, Any
4 | | from datetime import datetime
5 | | from uuid import UUID
6 | |
7 | | from pydantic import BaseModel, Field
  | |_____________________________________^
  |
help: Organize imports

F401 [*] `typing.List` imported but unused
 --> src/agent_workbench/models/schemas.py:3:20
  |
1 | """Pydantic schemas for Agent Workbench API."""
2 |
3 | from typing import List, Optional, Dict, Any
  |                    ^^^^
4 | from datetime import datetime
5 | from uuid import UUID
  |
help: Remove unused import: `typing.List`

I001 [*] Import block is un-sorted or un-formatted
  --> tests/conftest.py:3:1
   |
 1 |   """Test configuration and fixtures for Agent Workbench."""
 2 |
 3 | / import pytest
 4 | | import asyncio
 5 | | from unittest.mock import MagicMock
 6 | |
 7 | | from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
 8 | | from sqlalchemy.orm import sessionmaker
 9 | |
10 | | from agent_workbench.models.database import Base
   | |________________________________________________^
   |
help: Organize imports

W291 [*] Trailing whitespace
  --> tests/conftest.py:38:22
   |
36 |     """Create a database session for testing."""
37 |     async_session_factory = sessionmaker(
38 |         async_engine, 
   |                      ^
39 |         class_=AsyncSession, 
40 |         expire_on_commit=False
   |
help: Remove trailing whitespace

W291 [*] Trailing whitespace
  --> tests/conftest.py:39:29
   |
37 |     async_session_factory = sessionmaker(
38 |         async_engine, 
39 |         class_=AsyncSession, 
   |                             ^
40 |         expire_on_commit=False
41 |     )
   |
help: Remove trailing whitespace

I001 [*] Import block is un-sorted or un-formatted
  --> tests/integration/test_database_operations.py:3:1
   |
 1 |   """Integration tests for database operations."""
 2 |
 3 | / import pytest
 4 | | import pytest_asyncio
 5 | | from uuid import uuid4
 6 | |
 7 | | from agent_workbench.models.database import (
 8 | |     ConversationModel, MessageModel, AgentConfigModel
 9 | | )
10 | | from agent_workbench.api.database import DatabaseManager
11 | | from agent_workbench.models.config import DatabaseConfig
   | |________________________________________________________^
   |
help: Organize imports

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:24:1
   |
22 |     await db_manager.initialize()
23 |     await db_manager.create_tables()
24 |     
   | ^^^^
25 |     yield db_manager
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:26:1
   |
25 |     yield db_manager
26 |     
   | ^^^^
27 |     await db_manager.close()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:45:1
   |
43 |     )
44 |     db_manager = DatabaseManager(config)
45 |     
   | ^^^^
46 |     # Should be able to initialize without errors
47 |     await db_manager.initialize()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:50:1
   |
48 |     assert db_manager.engine is not None
49 |     assert db_manager.session_factory is not None
50 |     
   | ^^^^
51 |     # Should be able to initialize again without errors
52 |     await db_manager.initialize()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:53:1
   |
51 |     # Should be able to initialize again without errors
52 |     await db_manager.initialize()
53 |     
   | ^^^^
54 |     await db_manager.close()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:67:1
   |
65 |             "title": "Integration Test Conversation"
66 |         }
67 |         
   | ^^^^^^^^
68 |         conversation = await ConversationModel.create(session, **conversation_data)
69 |         assert conversation.id is not None
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:72:1
   |
70 |         assert conversation.user_id == user_id
71 |         assert conversation.title == "Integration Test Conversation"
72 |         
   | ^^^^^^^^
73 |         # Retrieve conversation
74 |         retrieved_conversation = await ConversationModel.get_by_id(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:79:1
   |
77 |         assert retrieved_conversation is not None
78 |         assert retrieved_conversation.id == conversation.id
79 |         
   | ^^^^^^^^
80 |         # Update conversation
81 |         updated_conversation = await conversation.update(
   |
help: Remove whitespace from blank line

W291 [*] Trailing whitespace
  --> tests/integration/test_database_operations.py:82:21
   |
80 |         # Update conversation
81 |         updated_conversation = await conversation.update(
82 |             session, 
   |                     ^
83 |             title="Updated Test Conversation"
84 |         )
   |
help: Remove trailing whitespace

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:86:1
   |
84 |         )
85 |         assert updated_conversation.title == "Updated Test Conversation"
86 |         
   | ^^^^^^^^
87 |         # Delete conversation
88 |         await conversation.delete(session)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/integration/test_database_operations.py:89:1
   |
87 |         # Delete conversation
88 |         await conversation.delete(session)
89 |         
   | ^^^^^^^^
90 |         # Verify deletion
91 |         deleted_conversation = await ConversationModel.get_by_id(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:107:1
    |
105 |             title="Test Conversation for Messages"
106 |         )
107 |         
    | ^^^^^^^^
108 |         # Create message
109 |         message_data = {
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:115:1
    |
113 |             "metadata_": {"test": "value"}
114 |         }
115 |         
    | ^^^^^^^^
116 |         message = await MessageModel.create(session, **message_data)
117 |         assert message.id is not None
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:121:1
    |
119 |         assert message.role == "user"
120 |         assert message.content == "Test message content for integration"
121 |         
    | ^^^^^^^^
122 |         # Retrieve message
123 |         retrieved_message = await MessageModel.get_by_id(session, message.id)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:126:1
    |
124 |         assert retrieved_message is not None
125 |         assert retrieved_message.id == message.id
126 |         
    | ^^^^^^^^
127 |         # Get messages by conversation
128 |         messages = await MessageModel.get_by_conversation(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:133:1
    |
131 |         assert len(messages) == 1
132 |         assert messages[0].id == message.id
133 |         
    | ^^^^^^^^
134 |         # Update message
135 |         updated_message = await message.update(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:140:1
    |
138 |         )
139 |         assert updated_message.content == "Updated message content"
140 |         
    | ^^^^^^^^
141 |         # Delete message
142 |         await message.delete(session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:143:1
    |
141 |         # Delete message
142 |         await message.delete(session)
143 |         
    | ^^^^^^^^
144 |         # Verify deletion
145 |         deleted_message = await MessageModel.get_by_id(session, message.id)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:163:1
    |
161 |             }
162 |         }
163 |         
    | ^^^^^^^^
164 |         agent_config = await AgentConfigModel.create(session, **config_data)
165 |         assert agent_config.id is not None
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:168:1
    |
166 |         assert agent_config.name == "Integration Test Config"
167 |         assert agent_config.config["model"] == "gpt-4"
168 |         
    | ^^^^^^^^
169 |         # Retrieve agent configuration
170 |         retrieved_config = await AgentConfigModel.get_by_id(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:175:1
    |
173 |         assert retrieved_config is not None
174 |         assert retrieved_config.id == agent_config.id
175 |         
    | ^^^^^^^^
176 |         # Get all configurations
177 |         all_configs = await AgentConfigModel.get_all(session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:180:1
    |
178 |         assert len(all_configs) == 1
179 |         assert all_configs[0].id == agent_config.id
180 |         
    | ^^^^^^^^
181 |         # Update agent configuration
182 |         updated_config = await agent_config.update(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:189:1
    |
187 |         assert updated_config.name == "Updated Test Config"
188 |         assert updated_config.description == "Updated description"
189 |         
    | ^^^^^^^^
190 |         # Delete agent configuration
191 |         await agent_config.delete(session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:192:1
    |
190 |         # Delete agent configuration
191 |         await agent_config.delete(session)
192 |         
    | ^^^^^^^^
193 |         # Verify deletion
194 |         deleted_config = await AgentConfigModel.get_by_id(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:210:1
    |
208 |             title="Multi-message Test Conversation"
209 |         )
210 |         
    | ^^^^^^^^
211 |         # Create multiple messages
212 |         message1 = await MessageModel.create(
    |
help: Remove whitespace from blank line

F841 Local variable `message1` is assigned to but never used
   --> tests/integration/test_database_operations.py:212:9
    |
211 |         # Create multiple messages
212 |         message1 = await MessageModel.create(
    |         ^^^^^^^^
213 |             session,
214 |             conversation_id=conversation.id,
    |
help: Remove assignment to unused variable `message1`

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:218:1
    |
216 |             content="First message"
217 |         )
218 |         
    | ^^^^^^^^
219 |         message2 = await MessageModel.create(
220 |             session,
    |
help: Remove whitespace from blank line

F841 Local variable `message2` is assigned to but never used
   --> tests/integration/test_database_operations.py:219:9
    |
217 |         )
218 |         
219 |         message2 = await MessageModel.create(
    |         ^^^^^^^^
220 |             session,
221 |             conversation_id=conversation.id,
    |
help: Remove assignment to unused variable `message2`

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:225:1
    |
223 |             content="Second message"
224 |         )
225 |         
    | ^^^^^^^^
226 |         message3 = await MessageModel.create(
227 |             session,
    |
help: Remove whitespace from blank line

F841 Local variable `message3` is assigned to but never used
   --> tests/integration/test_database_operations.py:226:9
    |
224 |         )
225 |         
226 |         message3 = await MessageModel.create(
    |         ^^^^^^^^
227 |             session,
228 |             conversation_id=conversation.id,
    |
help: Remove assignment to unused variable `message3`

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:232:1
    |
230 |             content="Third message"
231 |         )
232 |         
    | ^^^^^^^^
233 |         # Get all messages for conversation
234 |         messages = await MessageModel.get_by_conversation(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:238:1
    |
236 |         )
237 |         assert len(messages) == 3
238 |         
    | ^^^^^^^^
239 |         # Messages should be ordered by creation time
240 |         assert messages[0].content == "First message"
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:243:1
    |
241 |         assert messages[1].content == "Second message"
242 |         assert messages[2].content == "Third message"
243 |         
    | ^^^^^^^^
244 |         # Delete conversation (should cascade delete messages)
245 |         await conversation.delete(session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:246:1
    |
244 |         # Delete conversation (should cascade delete messages)
245 |         await conversation.delete(session)
246 |         
    | ^^^^^^^^
247 |         # Verify messages are also deleted
248 |         conversation_messages = await MessageModel.get_by_conversation(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:264:1
    |
262 |     db_manager = DatabaseManager(config)
263 |     await db_manager.initialize()
264 |     
    | ^^^^
265 |     # Should be able to check connection when database is available
266 |     is_connected = await db_manager.check_database_connection()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:268:1
    |
266 |     is_connected = await db_manager.check_database_connection()
267 |     assert is_connected is True
268 |     
    | ^^^^
269 |     # Close the database and check again
270 |     await db_manager.close()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/integration/test_database_operations.py:273:1
    |
271 |     is_connected = await db_manager.check_database_connection()
272 |     assert is_connected is False
273 |     
    | ^^^^
274 |     # Clean up
275 |     await db_manager.close()
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
 --> tests/test_health.py:1:1
  |
1 | / from fastapi.testclient import TestClient
2 | | from agent_workbench.main import app
  | |____________________________________^
  |
help: Organize imports

I001 [*] Import block is un-sorted or un-formatted
  --> tests/unit/api/test_agent_configs.py:3:1
   |
 1 |   """Unit tests for agent configuration API routes."""
 2 |
 3 | / import pytest
 4 | | from uuid import uuid4, UUID
 5 | | from unittest.mock import AsyncMock, MagicMock
 6 | |
 7 | | from fastapi import FastAPI
 8 | | from fastapi.testclient import TestClient
 9 | | from sqlalchemy.ext.asyncio import AsyncSession
10 | |
11 | | from agent_workbench.api.routes.agent_configs import router
12 | | from agent_workbench.models.database import AgentConfigModel
13 | | from agent_workbench.models.schemas import AgentConfigResponse
   | |______________________________________________________________^
   |
help: Organize imports

F401 [*] `agent_workbench.models.database.AgentConfigModel` imported but unused
  --> tests/unit/api/test_agent_configs.py:12:45
   |
11 | from agent_workbench.api.routes.agent_configs import router
12 | from agent_workbench.models.database import AgentConfigModel
   |                                             ^^^^^^^^^^^^^^^^
13 | from agent_workbench.models.schemas import AgentConfigResponse
   |
help: Remove unused import: `agent_workbench.models.database.AgentConfigModel`

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:42:1
   |
40 |     mock_result = MagicMock()
41 |     mock_result.scalar_one_or_none.return_value = None
42 |     
   | ^^^^
43 |     # Mock the select function properly
44 |     mock_select = mocker.patch('sqlalchemy.select')
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:46:1
   |
44 |     mock_select = mocker.patch('sqlalchemy.select')
45 |     mock_select.return_value.where.return_value = MagicMock()
46 |     
   | ^^^^
47 |     mocker.patch(
48 |         'sqlalchemy.ext.asyncio.AsyncSession.execute',
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:51:1
   |
49 |         return_value=mock_result
50 |     )
51 |     
   | ^^^^
52 |     # Mock the AgentConfigModel.create method
53 |     mock_agent_config = MagicMock()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:60:1
   |
58 |     mock_agent_config.created_at = "2025-01-01T00:00:00"
59 |     mock_agent_config.updated_at = "2025-01-01T00:00:00"
60 |     
   | ^^^^
61 |     mocker.patch(
62 |         'agent_workbench.models.database.AgentConfigModel.create',
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:65:1
   |
63 |         return_value=mock_agent_config
64 |     )
65 |     
   | ^^^^
66 |     # Mock the AgentConfigResponse.model_validate method
67 |     mocker.patch(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:78:1
   |
76 |         )
77 |     )
78 |     
   | ^^^^
79 |     response = client.post(
80 |         "/api/v1/agent-configs/",
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_agent_configs.py:87:1
   |
85 |         }
86 |     )
87 |     
   | ^^^^
88 |     assert response.status_code == 201
89 |     assert "id" in response.json()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:98:1
    |
 96 |     mock_existing_config = MagicMock()
 97 |     mock_existing_config.name = "Test Agent Config"
 98 |     
    | ^^^^
 99 |     mock_result = MagicMock()
100 |     mock_result.scalar_one_or_none.return_value = mock_existing_config
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:101:1
    |
 99 |     mock_result = MagicMock()
100 |     mock_result.scalar_one_or_none.return_value = mock_existing_config
101 |     
    | ^^^^
102 |     mocker.patch(
103 |         'sqlalchemy.ext.asyncio.AsyncSession.execute',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:106:1
    |
104 |         return_value=mock_result
105 |     )
106 |     
    | ^^^^
107 |     response = client.post(
108 |         "/api/v1/agent-configs/",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:114:1
    |
112 |         }
113 |     )
114 |     
    | ^^^^
115 |     assert response.status_code == 409
116 |     assert "already exists" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:122:1
    |
120 |     """Test successful agent configuration retrieval."""
121 |     config_id = str(uuid4())
122 |     
    | ^^^^
123 |     # Mock the AgentConfigModel.get_by_id method
124 |     mock_agent_config = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:131:1
    |
129 |     mock_agent_config.created_at = "2025-01-01T00:00:00"
130 |     mock_agent_config.updated_at = "2025-01-01T00:00:00"
131 |     
    | ^^^^
132 |     mocker.patch(
133 |         'agent_workbench.models.database.AgentConfigModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:136:1
    |
134 |         return_value=mock_agent_config
135 |     )
136 |     
    | ^^^^
137 |     # Mock the AgentConfigResponse.model_validate method
138 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:149:1
    |
147 |         )
148 |     )
149 |     
    | ^^^^
150 |     response = client.get(f"/api/v1/agent-configs/{config_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:151:1
    |
150 |     response = client.get(f"/api/v1/agent-configs/{config_id}")
151 |     
    | ^^^^
152 |     assert response.status_code == 200
153 |     assert response.json()["id"] == config_id
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:159:1
    |
157 |     """Test agent configuration not found error."""
158 |     config_id = str(uuid4())
159 |     
    | ^^^^
160 |     # Mock the AgentConfigModel.get_by_id method to return None
161 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:165:1
    |
163 |         return_value=None
164 |     )
165 |     
    | ^^^^
166 |     response = client.get(f"/api/v1/agent-configs/{config_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:167:1
    |
166 |     response = client.get(f"/api/v1/agent-configs/{config_id}")
167 |     
    | ^^^^
168 |     assert response.status_code == 404
169 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:182:1
    |
180 |     mock_config1.created_at = "2025-01-01T00:00:00"
181 |     mock_config1.updated_at = "2025-01-01T00:00:00"
182 |     
    | ^^^^
183 |     mock_config2 = MagicMock()
184 |     mock_config2.id = uuid4()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:190:1
    |
188 |     mock_config2.created_at = "2025-01-01T00:00:00"
189 |     mock_config2.updated_at = "2025-01-01T00:00:00"
190 |     
    | ^^^^
191 |     mocker.patch(
192 |         'agent_workbench.models.database.AgentConfigModel.get_all',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:195:1
    |
193 |         return_value=[mock_config1, mock_config2]
194 |     )
195 |     
    | ^^^^
196 |     # Mock the AgentConfigResponse.model_validate method
197 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:218:1
    |
216 |         ]
217 |     )
218 |     
    | ^^^^
219 |     response = client.get("/api/v1/agent-configs/")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:220:1
    |
219 |     response = client.get("/api/v1/agent-configs/")
220 |     
    | ^^^^
221 |     assert response.status_code == 200
222 |     assert len(response.json()) == 2
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:230:1
    |
228 |     """Test successful agent configuration update."""
229 |     config_id = str(uuid4())
230 |     
    | ^^^^
231 |     # Mock the AgentConfigModel.get_by_id method
232 |     mock_agent_config = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:239:1
    |
237 |     mock_agent_config.created_at = "2025-01-01T00:00:00"
238 |     mock_agent_config.updated_at = "2025-01-01T00:00:00"
239 |     
    | ^^^^
240 |     mocker.patch(
241 |         'agent_workbench.models.database.AgentConfigModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:244:1
    |
242 |         return_value=mock_agent_config
243 |     )
244 |     
    | ^^^^
245 |     # Mock the session.execute method to return None (no conflicting config)
246 |     mock_result = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:252:1
    |
250 |         return_value=mock_result
251 |     )
252 |     
    | ^^^^
253 |     # Mock the agent_config.update method
254 |     updated_config = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:261:1
    |
259 |     updated_config.created_at = mock_agent_config.created_at
260 |     updated_config.updated_at = "2025-01-02T00:00:00"
261 |     
    | ^^^^
262 |     # Make the update method awaitable
263 |     mock_update = mocker.AsyncMock(return_value=updated_config)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:265:1
    |
263 |     mock_update = mocker.AsyncMock(return_value=updated_config)
264 |     mock_agent_config.update = mock_update
265 |     
    | ^^^^
266 |     mocker.patch.object(
267 |         mock_agent_config,
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:271:1
    |
269 |         mock_update
270 |     )
271 |     
    | ^^^^
272 |     # Mock the AgentConfigResponse.model_validate method
273 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:284:1
    |
282 |         )
283 |     )
284 |     
    | ^^^^
285 |     response = client.put(
286 |         f"/api/v1/agent-configs/{config_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:289:1
    |
287 |         json={"name": "Updated Name", "description": "Updated description"}
288 |     )
289 |     
    | ^^^^
290 |     assert response.status_code == 200
291 |     assert response.json()["name"] == "Updated Name"
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:297:1
    |
295 |     """Test agent configuration update with not found error."""
296 |     config_id = str(uuid4())
297 |     
    | ^^^^
298 |     # Mock the AgentConfigModel.get_by_id method to return None
299 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:303:1
    |
301 |         return_value=None
302 |     )
303 |     
    | ^^^^
304 |     response = client.put(
305 |         f"/api/v1/agent-configs/{config_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:308:1
    |
306 |         json={"name": "Updated Name"}
307 |     )
308 |     
    | ^^^^
309 |     assert response.status_code == 404
310 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:316:1
    |
314 |     """Test agent configuration update with conflict."""
315 |     config_id = str(uuid4())
316 |     
    | ^^^^
317 |     # Mock the AgentConfigModel.get_by_id method
318 |     mock_agent_config = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:321:1
    |
319 |     mock_agent_config.id = UUID(config_id)
320 |     mock_agent_config.name = "Original Name"
321 |     
    | ^^^^
322 |     mocker.patch(
323 |         'agent_workbench.models.database.AgentConfigModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:326:1
    |
324 |         return_value=mock_agent_config
325 |     )
326 |     
    | ^^^^
327 |     # Mock the session.execute method to return a conflicting config
328 |     mock_conflicting_config = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:331:1
    |
329 |     mock_conflicting_config.id = uuid4()  # Different ID
330 |     mock_conflicting_config.name = "Updated Name"
331 |     
    | ^^^^
332 |     mock_result = MagicMock()
333 |     mock_result.scalar_one_or_none.return_value = mock_conflicting_config
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:334:1
    |
332 |     mock_result = MagicMock()
333 |     mock_result.scalar_one_or_none.return_value = mock_conflicting_config
334 |     
    | ^^^^
335 |     mocker.patch(
336 |         'sqlalchemy.ext.asyncio.AsyncSession.execute',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:339:1
    |
337 |         return_value=mock_result
338 |     )
339 |     
    | ^^^^
340 |     response = client.put(
341 |         f"/api/v1/agent-configs/{config_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:344:1
    |
342 |         json={"name": "Updated Name"}
343 |     )
344 |     
    | ^^^^
345 |     assert response.status_code == 409
346 |     assert "already exists" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:352:1
    |
350 |     """Test successful agent configuration deletion."""
351 |     config_id = str(uuid4())
352 |     
    | ^^^^
353 |     # Mock the AgentConfigModel.get_by_id method
354 |     mock_agent_config = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:356:1
    |
354 |     mock_agent_config = MagicMock()
355 |     mock_agent_config.id = UUID(config_id)
356 |     
    | ^^^^
357 |     mocker.patch(
358 |         'agent_workbench.models.database.AgentConfigModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:361:1
    |
359 |         return_value=mock_agent_config
360 |     )
361 |     
    | ^^^^
362 |     # Mock the agent_config.delete method to be awaitable
363 |     mock_delete = mocker.AsyncMock(return_value=None)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:365:1
    |
363 |     mock_delete = mocker.AsyncMock(return_value=None)
364 |     mock_agent_config.delete = mock_delete
365 |     
    | ^^^^
366 |     mocker.patch.object(
367 |         mock_agent_config,
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:371:1
    |
369 |         mock_delete
370 |     )
371 |     
    | ^^^^
372 |     response = client.delete(f"/api/v1/agent-configs/{config_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:373:1
    |
372 |     response = client.delete(f"/api/v1/agent-configs/{config_id}")
373 |     
    | ^^^^
374 |     assert response.status_code == 204
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:380:1
    |
378 |     """Test agent configuration deletion with not found error."""
379 |     config_id = str(uuid4())
380 |     
    | ^^^^
381 |     # Mock the AgentConfigModel.get_by_id method to return None
382 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:386:1
    |
384 |         return_value=None
385 |     )
386 |     
    | ^^^^
387 |     response = client.delete(f"/api/v1/agent-configs/{config_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_agent_configs.py:388:1
    |
387 |     response = client.delete(f"/api/v1/agent-configs/{config_id}")
388 |     
    | ^^^^
389 |     assert response.status_code == 404
390 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> tests/unit/api/test_conversations.py:3:1
   |
 1 |   """Unit tests for conversation API routes."""
 2 |
 3 | / import pytest
 4 | | from uuid import uuid4, UUID
 5 | | from unittest.mock import AsyncMock, MagicMock
 6 | |
 7 | | from fastapi import FastAPI
 8 | | from fastapi.testclient import TestClient
 9 | | from sqlalchemy.ext.asyncio import AsyncSession
10 | |
11 | | from agent_workbench.api.routes.conversations import router
12 | | from agent_workbench.models.schemas import ConversationResponse
   | |_______________________________________________________________^
   |
help: Organize imports

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_conversations.py:63:1
   |
61 |     mock_conversation.created_at = "2025-01-01T00:00:00"
62 |     mock_conversation.updated_at = "2025-01-01T00:00:00"
63 |     
   | ^^^^
64 |     mocker.patch(
65 |         'agent_workbench.models.database.ConversationModel.create',
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_conversations.py:68:1
   |
66 |         return_value=mock_conversation
67 |     )
68 |     
   | ^^^^
69 |     # Mock the ConversationResponse.model_validate method
70 |     mocker.patch(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_conversations.py:80:1
   |
78 |         )
79 |     )
80 |     
   | ^^^^
81 |     response = client.post(
82 |         "/api/v1/conversations/",
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_conversations.py:85:1
   |
83 |         json={"user_id": str(uuid4()), "title": "Test Conversation"}
84 |     )
85 |     
   | ^^^^
86 |     assert response.status_code == 201
87 |     assert "id" in response.json()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_conversations.py:94:1
   |
92 |     """Test successful conversation retrieval."""
93 |     conversation_id = str(uuid4())
94 |     
   | ^^^^
95 |     # Mock the ConversationModel.get_by_id method
96 |     mock_conversation = MagicMock()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:102:1
    |
100 |     mock_conversation.created_at = "2025-01-01T00:00:00"
101 |     mock_conversation.updated_at = "2025-01-01T00:00:00"
102 |     
    | ^^^^
103 |     mocker.patch(
104 |         'agent_workbench.models.database.ConversationModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:107:1
    |
105 |         return_value=mock_conversation
106 |     )
107 |     
    | ^^^^
108 |     # Mock the ConversationResponse.model_validate method
109 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:119:1
    |
117 |         )
118 |     )
119 |     
    | ^^^^
120 |     response = client.get(f"/api/v1/conversations/{conversation_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:121:1
    |
120 |     response = client.get(f"/api/v1/conversations/{conversation_id}")
121 |     
    | ^^^^
122 |     assert response.status_code == 200
123 |     assert response.json()["id"] == conversation_id
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:129:1
    |
127 |     """Test conversation not found error."""
128 |     conversation_id = str(uuid4())
129 |     
    | ^^^^
130 |     # Mock the ConversationModel.get_by_id method to return None
131 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:135:1
    |
133 |         return_value=None
134 |     )
135 |     
    | ^^^^
136 |     response = client.get(f"/api/v1/conversations/{conversation_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:137:1
    |
136 |     response = client.get(f"/api/v1/conversations/{conversation_id}")
137 |     
    | ^^^^
138 |     assert response.status_code == 404
139 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:151:1
    |
149 |     mock_conversation1.created_at = "2025-01-01T00:00:00"
150 |     mock_conversation1.updated_at = "2025-01-01T00:00:00"
151 |     
    | ^^^^
152 |     mock_conversation2 = MagicMock()
153 |     mock_conversation2.id = uuid4()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:158:1
    |
156 |     mock_conversation2.created_at = "2025-01-01T00:00:00"
157 |     mock_conversation2.updated_at = "2025-01-01T00:00:00"
158 |     
    | ^^^^
159 |     mock_result = MagicMock()
160 |     mock_result.scalars().all.return_value = [mock_conversation1, mock_conversation2]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:161:1
    |
159 |     mock_result = MagicMock()
160 |     mock_result.scalars().all.return_value = [mock_conversation1, mock_conversation2]
161 |     
    | ^^^^
162 |     mocker.patch(
163 |         'sqlalchemy.ext.asyncio.AsyncSession.execute',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:166:1
    |
164 |         return_value=mock_result
165 |     )
166 |     
    | ^^^^
167 |     # Mock the ConversationResponse.model_validate method
168 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:187:1
    |
185 |         ]
186 |     )
187 |     
    | ^^^^
188 |     response = client.get("/api/v1/conversations/")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:189:1
    |
188 |     response = client.get("/api/v1/conversations/")
189 |     
    | ^^^^
190 |     assert response.status_code == 200
191 |     assert len(response.json()) == 2
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:199:1
    |
197 |     """Test successful conversation update."""
198 |     conversation_id = str(uuid4())
199 |     
    | ^^^^
200 |     # Mock the ConversationModel.get_by_id method
201 |     mock_conversation = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:207:1
    |
205 |     mock_conversation.created_at = "2025-01-01T00:00:00"
206 |     mock_conversation.updated_at = "2025-01-01T00:00:00"
207 |     
    | ^^^^
208 |     mocker.patch(
209 |         'agent_workbench.models.database.ConversationModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:212:1
    |
210 |         return_value=mock_conversation
211 |     )
212 |     
    | ^^^^
213 |     # Mock the conversation.update method
214 |     updated_conversation = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:220:1
    |
218 |     updated_conversation.created_at = mock_conversation.created_at
219 |     updated_conversation.updated_at = "2025-01-02T00:00:00"
220 |     
    | ^^^^
221 |     # Make the update method awaitable
222 |     mock_update = mocker.AsyncMock(return_value=updated_conversation)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:224:1
    |
222 |     mock_update = mocker.AsyncMock(return_value=updated_conversation)
223 |     mock_conversation.update = mock_update
224 |     
    | ^^^^
225 |     mocker.patch.object(
226 |         mock_conversation,
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:230:1
    |
228 |         mock_update
229 |     )
230 |     
    | ^^^^
231 |     # Mock the ConversationResponse.model_validate method
232 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:242:1
    |
240 |         )
241 |     )
242 |     
    | ^^^^
243 |     response = client.put(
244 |         f"/api/v1/conversations/{conversation_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:247:1
    |
245 |         json={"title": "Updated Title"}
246 |     )
247 |     
    | ^^^^
248 |     assert response.status_code == 200
249 |     assert response.json()["title"] == "Updated Title"
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:255:1
    |
253 |     """Test conversation update with not found error."""
254 |     conversation_id = str(uuid4())
255 |     
    | ^^^^
256 |     # Mock the ConversationModel.get_by_id method to return None
257 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:261:1
    |
259 |         return_value=None
260 |     )
261 |     
    | ^^^^
262 |     response = client.put(
263 |         f"/api/v1/conversations/{conversation_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:266:1
    |
264 |         json={"title": "Updated Title"}
265 |     )
266 |     
    | ^^^^
267 |     assert response.status_code == 404
268 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:274:1
    |
272 |     """Test successful conversation deletion."""
273 |     conversation_id = str(uuid4())
274 |     
    | ^^^^
275 |     # Mock the ConversationModel.get_by_id method
276 |     mock_conversation = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:278:1
    |
276 |     mock_conversation = MagicMock()
277 |     mock_conversation.id = UUID(conversation_id)
278 |     
    | ^^^^
279 |     mocker.patch(
280 |         'agent_workbench.models.database.ConversationModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:283:1
    |
281 |         return_value=mock_conversation
282 |     )
283 |     
    | ^^^^
284 |     # Mock the conversation.delete method to be awaitable
285 |     mock_delete = mocker.AsyncMock(return_value=None)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:287:1
    |
285 |     mock_delete = mocker.AsyncMock(return_value=None)
286 |     mock_conversation.delete = mock_delete
287 |     
    | ^^^^
288 |     mocker.patch.object(
289 |         mock_conversation,
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:293:1
    |
291 |         mock_delete
292 |     )
293 |     
    | ^^^^
294 |     response = client.delete(f"/api/v1/conversations/{conversation_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:295:1
    |
294 |     response = client.delete(f"/api/v1/conversations/{conversation_id}")
295 |     
    | ^^^^
296 |     assert response.status_code == 204
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:302:1
    |
300 |     """Test conversation deletion with not found error."""
301 |     conversation_id = str(uuid4())
302 |     
    | ^^^^
303 |     # Mock the ConversationModel.get_by_id method to return None
304 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:308:1
    |
306 |         return_value=None
307 |     )
308 |     
    | ^^^^
309 |     response = client.delete(f"/api/v1/conversations/{conversation_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_conversations.py:310:1
    |
309 |     response = client.delete(f"/api/v1/conversations/{conversation_id}")
310 |     
    | ^^^^
311 |     assert response.status_code == 404
312 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> tests/unit/api/test_health.py:3:1
   |
 1 |   """Unit tests for health check API routes."""
 2 |
 3 | / import pytest
 4 | | from unittest.mock import AsyncMock, MagicMock
 5 | | from datetime import datetime
 6 | |
 7 | | from fastapi import FastAPI
 8 | | from fastapi.testclient import TestClient
 9 | | from sqlalchemy.ext.asyncio import AsyncSession
10 | |
11 | | from src.agent_workbench.api.routes.health import router
   | |________________________________________________________^
   |
help: Organize imports

F401 [*] `unittest.mock.MagicMock` imported but unused
 --> tests/unit/api/test_health.py:4:38
  |
3 | import pytest
4 | from unittest.mock import AsyncMock, MagicMock
  |                                      ^^^^^^^^^
5 | from datetime import datetime
  |
help: Remove unused import: `unittest.mock.MagicMock`

F401 [*] `datetime.datetime` imported but unused
 --> tests/unit/api/test_health.py:5:22
  |
3 | import pytest
4 | from unittest.mock import AsyncMock, MagicMock
5 | from datetime import datetime
  |                      ^^^^^^^^
6 |
7 | from fastapi import FastAPI
  |
help: Remove unused import: `datetime.datetime`

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_health.py:41:1
   |
39 |         return_value=True
40 |     )
41 |     
   | ^^^^
42 |     response = client.get("/api/v1/health/")
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_health.py:43:1
   |
42 |     response = client.get("/api/v1/health/")
43 |     
   | ^^^^
44 |     assert response.status_code == 200
45 |     json_response = response.json()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_health.py:58:1
   |
56 |         return_value=False
57 |     )
58 |     
   | ^^^^
59 |     response = client.get("/api/v1/health/")
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_health.py:60:1
   |
59 |     response = client.get("/api/v1/health/")
60 |     
   | ^^^^
61 |     assert response.status_code == 200
62 |     json_response = response.json()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_health.py:71:1
   |
69 |     """Test ping endpoint."""
70 |     response = client.get("/api/v1/health/ping")
71 |     
   | ^^^^
72 |     assert response.status_code == 200
73 |     json_response = response.json()
   |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> tests/unit/api/test_messages.py:3:1
   |
 1 |   """Unit tests for message API routes."""
 2 |
 3 | / import pytest
 4 | | from uuid import uuid4, UUID
 5 | | from unittest.mock import AsyncMock, MagicMock
 6 | |
 7 | | from fastapi import FastAPI
 8 | | from fastapi.testclient import TestClient
 9 | | from sqlalchemy.ext.asyncio import AsyncSession
10 | |
11 | | from agent_workbench.api.routes.messages import router
12 | | from agent_workbench.models.schemas import MessageResponse
   | |__________________________________________________________^
   |
help: Organize imports

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:38:1
   |
36 |     """Test successful message creation."""
37 |     conversation_id = str(uuid4())
38 |     
   | ^^^^
39 |     # Mock the ConversationModel.get_by_id method
40 |     mock_conversation = MagicMock()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:42:1
   |
40 |     mock_conversation = MagicMock()
41 |     mock_conversation.id = UUID(conversation_id)
42 |     
   | ^^^^
43 |     mocker.patch(
44 |         'agent_workbench.models.database.ConversationModel.get_by_id',
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:47:1
   |
45 |         return_value=mock_conversation
46 |     )
47 |     
   | ^^^^
48 |     # Mock the MessageModel.create method
49 |     mock_message = MagicMock()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:56:1
   |
54 |     mock_message.metadata_ = {"key": "value"}
55 |     mock_message.created_at = "2025-01-01T00:00:00"
56 |     
   | ^^^^
57 |     mocker.patch(
58 |         'agent_workbench.models.database.MessageModel.create',
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:61:1
   |
59 |         return_value=mock_message
60 |     )
61 |     
   | ^^^^
62 |     # Mock the MessageResponse.model_validate method
63 |     mocker.patch(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:74:1
   |
72 |         )
73 |     )
74 |     
   | ^^^^
75 |     response = client.post(
76 |         "/api/v1/messages/",
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:84:1
   |
82 |         }
83 |     )
84 |     
   | ^^^^
85 |     assert response.status_code == 201
86 |     assert "id" in response.json()
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/api/test_messages.py:93:1
   |
91 |     """Test message creation with conversation not found."""
92 |     conversation_id = str(uuid4())
93 |     
   | ^^^^
94 |     # Mock the ConversationModel.get_by_id method to return None
95 |     mocker.patch(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:99:1
    |
 97 |         return_value=None
 98 |     )
 99 |     
    | ^^^^
100 |     response = client.post(
101 |         "/api/v1/messages/",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:108:1
    |
106 |         }
107 |     )
108 |     
    | ^^^^
109 |     assert response.status_code == 404
110 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:117:1
    |
115 |     message_id = str(uuid4())
116 |     conversation_id = str(uuid4())
117 |     
    | ^^^^
118 |     # Mock the MessageModel.get_by_id method
119 |     mock_message = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:126:1
    |
124 |     mock_message.metadata_ = {"key": "value"}
125 |     mock_message.created_at = "2025-01-01T00:00:00"
126 |     
    | ^^^^
127 |     mocker.patch(
128 |         'agent_workbench.models.database.MessageModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:131:1
    |
129 |         return_value=mock_message
130 |     )
131 |     
    | ^^^^
132 |     # Mock the MessageResponse.model_validate method
133 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:144:1
    |
142 |         )
143 |     )
144 |     
    | ^^^^
145 |     response = client.get(f"/api/v1/messages/{message_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:146:1
    |
145 |     response = client.get(f"/api/v1/messages/{message_id}")
146 |     
    | ^^^^
147 |     assert response.status_code == 200
148 |     assert response.json()["id"] == message_id
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:154:1
    |
152 |     """Test message not found error."""
153 |     message_id = str(uuid4())
154 |     
    | ^^^^
155 |     # Mock the MessageModel.get_by_id method to return None
156 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:160:1
    |
158 |         return_value=None
159 |     )
160 |     
    | ^^^^
161 |     response = client.get(f"/api/v1/messages/{message_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:162:1
    |
161 |     response = client.get(f"/api/v1/messages/{message_id}")
162 |     
    | ^^^^
163 |     assert response.status_code == 404
164 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:170:1
    |
168 |     """Test successful messages listing."""
169 |     conversation_id = str(uuid4())
170 |     
    | ^^^^
171 |     # Mock the ConversationModel.get_by_id method
172 |     mock_conversation = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:174:1
    |
172 |     mock_conversation = MagicMock()
173 |     mock_conversation.id = UUID(conversation_id)
174 |     
    | ^^^^
175 |     mocker.patch(
176 |         'agent_workbench.models.database.ConversationModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:179:1
    |
177 |         return_value=mock_conversation
178 |     )
179 |     
    | ^^^^
180 |     # Mock the MessageModel.get_by_conversation method
181 |     mock_message1 = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:187:1
    |
185 |     mock_message1.content = "First message"
186 |     mock_message1.created_at = "2025-01-01T00:00:00"
187 |     
    | ^^^^
188 |     mock_message2 = MagicMock()
189 |     mock_message2.id = uuid4()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:194:1
    |
192 |     mock_message2.content = "Second message"
193 |     mock_message2.created_at = "2025-01-01T00:01:00"
194 |     
    | ^^^^
195 |     mocker.patch(
196 |         'agent_workbench.models.database.MessageModel.get_by_conversation',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:199:1
    |
197 |         return_value=[mock_message1, mock_message2]
198 |     )
199 |     
    | ^^^^
200 |     # Mock the MessageResponse.model_validate method
201 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:220:1
    |
218 |         ]
219 |     )
220 |     
    | ^^^^
221 |     response = client.get(f"/api/v1/messages/?conversation_id={conversation_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:222:1
    |
221 |     response = client.get(f"/api/v1/messages/?conversation_id={conversation_id}")
222 |     
    | ^^^^
223 |     assert response.status_code == 200
224 |     assert len(response.json()) == 2
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:232:1
    |
230 |     """Test messages listing with conversation not found."""
231 |     conversation_id = str(uuid4())
232 |     
    | ^^^^
233 |     # Mock the ConversationModel.get_by_id method to return None
234 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:238:1
    |
236 |         return_value=None
237 |     )
238 |     
    | ^^^^
239 |     response = client.get(f"/api/v1/messages/?conversation_id={conversation_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:240:1
    |
239 |     response = client.get(f"/api/v1/messages/?conversation_id={conversation_id}")
240 |     
    | ^^^^
241 |     assert response.status_code == 404
242 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:249:1
    |
247 |     message_id = str(uuid4())
248 |     conversation_id = str(uuid4())
249 |     
    | ^^^^
250 |     # Mock the MessageModel.get_by_id method
251 |     mock_message = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:257:1
    |
255 |     mock_message.content = "Original content"
256 |     mock_message.created_at = "2025-01-01T00:00:00"
257 |     
    | ^^^^
258 |     mocker.patch(
259 |         'agent_workbench.models.database.MessageModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:262:1
    |
260 |         return_value=mock_message
261 |     )
262 |     
    | ^^^^
263 |     # Mock the message.update method
264 |     updated_message = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:270:1
    |
268 |     updated_message.content = "Updated content"
269 |     updated_message.created_at = mock_message.created_at
270 |     
    | ^^^^
271 |     # Make the update method awaitable
272 |     mock_update = mocker.AsyncMock(return_value=updated_message)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:274:1
    |
272 |     mock_update = mocker.AsyncMock(return_value=updated_message)
273 |     mock_message.update = mock_update
274 |     
    | ^^^^
275 |     mocker.patch.object(
276 |         mock_message,
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:280:1
    |
278 |         mock_update
279 |     )
280 |     
    | ^^^^
281 |     # Mock the MessageResponse.model_validate method
282 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:292:1
    |
290 |         )
291 |     )
292 |     
    | ^^^^
293 |     response = client.put(
294 |         f"/api/v1/messages/{message_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:297:1
    |
295 |         json={"content": "Updated content"}
296 |     )
297 |     
    | ^^^^
298 |     assert response.status_code == 200
299 |     assert response.json()["content"] == "Updated content"
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:305:1
    |
303 |     """Test message update with not found error."""
304 |     message_id = str(uuid4())
305 |     
    | ^^^^
306 |     # Mock the MessageModel.get_by_id method to return None
307 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:311:1
    |
309 |         return_value=None
310 |     )
311 |     
    | ^^^^
312 |     response = client.put(
313 |         f"/api/v1/messages/{message_id}",
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:316:1
    |
314 |         json={"content": "Updated content"}
315 |     )
316 |     
    | ^^^^
317 |     assert response.status_code == 404
318 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:324:1
    |
322 |     """Test successful message deletion."""
323 |     message_id = str(uuid4())
324 |     
    | ^^^^
325 |     # Mock the MessageModel.get_by_id method
326 |     mock_message = MagicMock()
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:328:1
    |
326 |     mock_message = MagicMock()
327 |     mock_message.id = UUID(message_id)
328 |     
    | ^^^^
329 |     mocker.patch(
330 |         'agent_workbench.models.database.MessageModel.get_by_id',
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:333:1
    |
331 |         return_value=mock_message
332 |     )
333 |     
    | ^^^^
334 |     # Mock the message.delete method to be awaitable
335 |     mock_delete = mocker.AsyncMock(return_value=None)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:337:1
    |
335 |     mock_delete = mocker.AsyncMock(return_value=None)
336 |     mock_message.delete = mock_delete
337 |     
    | ^^^^
338 |     mocker.patch.object(
339 |         mock_message,
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:343:1
    |
341 |         mock_delete
342 |     )
343 |     
    | ^^^^
344 |     response = client.delete(f"/api/v1/messages/{message_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:345:1
    |
344 |     response = client.delete(f"/api/v1/messages/{message_id}")
345 |     
    | ^^^^
346 |     assert response.status_code == 204
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:352:1
    |
350 |     """Test message deletion with not found error."""
351 |     message_id = str(uuid4())
352 |     
    | ^^^^
353 |     # Mock the MessageModel.get_by_id method to return None
354 |     mocker.patch(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:358:1
    |
356 |         return_value=None
357 |     )
358 |     
    | ^^^^
359 |     response = client.delete(f"/api/v1/messages/{message_id}")
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/api/test_messages.py:360:1
    |
359 |     response = client.delete(f"/api/v1/messages/{message_id}")
360 |     
    | ^^^^
361 |     assert response.status_code == 404
362 |     assert "not found" in response.json()["detail"]["detail"]
    |
help: Remove whitespace from blank line

I001 [*] Import block is un-sorted or un-formatted
  --> tests/unit/models/test_database.py:3:1
   |
 1 |   """Unit tests for database models."""
 2 |
 3 | / import pytest
 4 | | from uuid import UUID, uuid4
 5 | | from datetime import datetime
 6 | |
 7 | | from sqlalchemy.ext.asyncio import create_async_engine
 8 | | from sqlalchemy.orm import sessionmaker
 9 | | from sqlalchemy.ext.asyncio import AsyncSession
10 | |
11 | | from agent_workbench.models.database import (
12 | |     Base, ConversationModel, MessageModel, AgentConfigModel
13 | | )
   | |_^
   |
help: Organize imports

F401 [*] `uuid.UUID` imported but unused
 --> tests/unit/models/test_database.py:4:18
  |
3 | import pytest
4 | from uuid import UUID, uuid4
  |                  ^^^^
5 | from datetime import datetime
  |
help: Remove unused import: `uuid.UUID`

F401 [*] `datetime.datetime` imported but unused
 --> tests/unit/models/test_database.py:5:22
  |
3 | import pytest
4 | from uuid import UUID, uuid4
5 | from datetime import datetime
  |                      ^^^^^^^^
6 |
7 | from sqlalchemy.ext.asyncio import create_async_engine
  |
help: Remove unused import: `datetime.datetime`

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:46:1
   |
44 |         "title": "Test Conversation"
45 |     }
46 |     
   | ^^^^
47 |     conversation = await ConversationModel.create(async_session, **conversation_data)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:48:1
   |
47 |     conversation = await ConversationModel.create(async_session, **conversation_data)
48 |     
   | ^^^^
49 |     assert conversation.id is not None
50 |     assert conversation.user_id == conversation_data["user_id"]
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:65:1
   |
63 |     }
64 |     conversation = await ConversationModel.create(async_session, **conversation_data)
65 |     
   | ^^^^
66 |     # Get the conversation by ID
67 |     retrieved_conversation = await ConversationModel.get_by_id(
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:70:1
   |
68 |         async_session, conversation.id
69 |     )
70 |     
   | ^^^^
71 |     assert retrieved_conversation is not None
72 |     assert retrieved_conversation.id == conversation.id
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:81:1
   |
79 |     """Test getting conversations by user ID."""
80 |     user_id = uuid4()
81 |     
   | ^^^^
82 |     # Create multiple conversations for the same user
83 |     conversation_data_1 = {
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:91:1
   |
89 |         "title": "Test Conversation 2"
90 |     }
91 |     
   | ^^^^
92 |     await ConversationModel.create(async_session, **conversation_data_1)
93 |     await ConversationModel.create(async_session, **conversation_data_2)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:94:1
   |
92 |     await ConversationModel.create(async_session, **conversation_data_1)
93 |     await ConversationModel.create(async_session, **conversation_data_2)
94 |     
   | ^^^^
95 |     # Get conversations by user ID
96 |     conversations = await ConversationModel.get_by_user(async_session, user_id)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
  --> tests/unit/models/test_database.py:97:1
   |
95 |     # Get conversations by user ID
96 |     conversations = await ConversationModel.get_by_user(async_session, user_id)
97 |     
   | ^^^^
98 |     assert len(conversations) == 2
99 |     assert all(conv.user_id == user_id for conv in conversations)
   |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:111:1
    |
109 |     }
110 |     conversation = await ConversationModel.create(async_session, **conversation_data)
111 |     
    | ^^^^
112 |     # Update the conversation
113 |     update_data = {
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:117:1
    |
115 |     }
116 |     updated_conversation = await conversation.update(async_session, **update_data)
117 |     
    | ^^^^
118 |     assert updated_conversation.title == "Updated Title"
119 |     # Allow equal timestamps since operations happen quickly
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:132:1
    |
130 |     }
131 |     conversation = await ConversationModel.create(async_session, **conversation_data)
132 |     
    | ^^^^
133 |     # Delete the conversation
134 |     await conversation.delete(async_session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:135:1
    |
133 |     # Delete the conversation
134 |     await conversation.delete(async_session)
135 |     
    | ^^^^
136 |     # Try to get the deleted conversation
137 |     retrieved_conversation = await ConversationModel.get_by_id(
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:140:1
    |
138 |         async_session, conversation.id
139 |     )
140 |     
    | ^^^^
141 |     assert retrieved_conversation is None
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:153:1
    |
151 |     }
152 |     conversation = await ConversationModel.create(async_session, **conversation_data)
153 |     
    | ^^^^
154 |     # Create a message
155 |     message_data = {
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:161:1
    |
159 |         "metadata_": {"key": "value"}
160 |     }
161 |     
    | ^^^^
162 |     message = await MessageModel.create(async_session, **message_data)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:163:1
    |
162 |     message = await MessageModel.create(async_session, **message_data)
163 |     
    | ^^^^
164 |     assert message.id is not None
165 |     assert message.conversation_id == conversation.id
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:181:1
    |
179 |     }
180 |     conversation = await ConversationModel.create(async_session, **conversation_data)
181 |     
    | ^^^^
182 |     # Create multiple messages for the conversation
183 |     message_data_1 = {
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:193:1
    |
191 |         "content": "Second message"
192 |     }
193 |     
    | ^^^^
194 |     await MessageModel.create(async_session, **message_data_1)
195 |     await MessageModel.create(async_session, **message_data_2)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:196:1
    |
194 |     await MessageModel.create(async_session, **message_data_1)
195 |     await MessageModel.create(async_session, **message_data_2)
196 |     
    | ^^^^
197 |     # Get messages by conversation ID
198 |     messages = await MessageModel.get_by_conversation(async_session, conversation.id)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:199:1
    |
197 |     # Get messages by conversation ID
198 |     messages = await MessageModel.get_by_conversation(async_session, conversation.id)
199 |     
    | ^^^^
200 |     assert len(messages) == 2
201 |     assert messages[0].content == "First message"
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:214:1
    |
212 |     }
213 |     conversation = await ConversationModel.create(async_session, **conversation_data)
214 |     
    | ^^^^
215 |     # Create a message
216 |     message_data = {
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:222:1
    |
220 |     }
221 |     message = await MessageModel.create(async_session, **message_data)
222 |     
    | ^^^^
223 |     # Get the message by ID
224 |     retrieved_message = await MessageModel.get_by_id(async_session, message.id)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:225:1
    |
223 |     # Get the message by ID
224 |     retrieved_message = await MessageModel.get_by_id(async_session, message.id)
225 |     
    | ^^^^
226 |     assert retrieved_message is not None
227 |     assert retrieved_message.id == message.id
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:243:1
    |
241 |         }
242 |     }
243 |     
    | ^^^^
244 |     agent_config = await AgentConfigModel.create(async_session, **config_data)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:245:1
    |
244 |     agent_config = await AgentConfigModel.create(async_session, **config_data)
245 |     
    | ^^^^
246 |     assert agent_config.id is not None
247 |     assert agent_config.name == config_data["name"]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:263:1
    |
261 |     }
262 |     agent_config = await AgentConfigModel.create(async_session, **config_data)
263 |     
    | ^^^^
264 |     # Get the agent configuration by ID
265 |     retrieved_config = await AgentConfigModel.get_by_id(async_session, agent_config.id)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:266:1
    |
264 |     # Get the agent configuration by ID
265 |     retrieved_config = await AgentConfigModel.get_by_id(async_session, agent_config.id)
266 |     
    | ^^^^
267 |     assert retrieved_config is not None
268 |     assert retrieved_config.id == agent_config.id
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:284:1
    |
282 |         "config": {"model": "gpt-3.5-turbo"}
283 |     }
284 |     
    | ^^^^
285 |     await AgentConfigModel.create(async_session, **config_data_1)
286 |     await AgentConfigModel.create(async_session, **config_data_2)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:287:1
    |
285 |     await AgentConfigModel.create(async_session, **config_data_1)
286 |     await AgentConfigModel.create(async_session, **config_data_2)
287 |     
    | ^^^^
288 |     # Get all agent configurations
289 |     agent_configs = await AgentConfigModel.get_all(async_session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:290:1
    |
288 |     # Get all agent configurations
289 |     agent_configs = await AgentConfigModel.get_all(async_session)
290 |     
    | ^^^^
291 |     assert len(agent_configs) == 2
292 |     config_names = [config.name for config in agent_configs]
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:306:1
    |
304 |     }
305 |     agent_config = await AgentConfigModel.create(async_session, **config_data)
306 |     
    | ^^^^
307 |     # Update the agent configuration
308 |     update_data = {
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:313:1
    |
311 |     }
312 |     updated_config = await agent_config.update(async_session, **update_data)
313 |     
    | ^^^^
314 |     assert updated_config.name == "Updated Name"
315 |     assert updated_config.description == "Updated description"
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:329:1
    |
327 |     }
328 |     agent_config = await AgentConfigModel.create(async_session, **config_data)
329 |     
    | ^^^^
330 |     # Delete the agent configuration
331 |     await agent_config.delete(async_session)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:332:1
    |
330 |     # Delete the agent configuration
331 |     await agent_config.delete(async_session)
332 |     
    | ^^^^
333 |     # Try to get the deleted agent configuration
334 |     retrieved_config = await AgentConfigModel.get_by_id(async_session, agent_config.id)
    |
help: Remove whitespace from blank line

W293 [*] Blank line contains whitespace
   --> tests/unit/models/test_database.py:335:1
    |
333 |     # Try to get the deleted agent configuration
334 |     retrieved_config = await AgentConfigModel.get_by_id(async_session, agent_config.id)
335 |     
    | ^^^^
336 |     assert retrieved_config is None
    |
help: Remove whitespace from blank line

Found 388 errors.
[*] 384 fixable with the `--fix` option (3 hidden fixes can be enabled with the `--unsafe-fixes` option).
🔬 Checking types...
src/agent_workbench/main.py:1: error: Cannot find implementation or library stub for module named "fastapi"  [import-not-found]
src/agent_workbench/main.py:15: error: Cannot find implementation or library stub for module named "uvicorn"  [import-not-found]
src/agent_workbench/models/config.py:4: error: Cannot find implementation or library stub for module named "pydantic"  [import-not-found]
src/agent_workbench/api/exceptions.py:4: error: Cannot find implementation or library stub for module named "fastapi"  [import-not-found]
src/agent_workbench/__main__.py:2: error: Cannot find implementation or library stub for module named "uvicorn"  [import-not-found]
src/agent_workbench/models/database.py:6: error: Cannot find implementation or library stub for module named "sqlalchemy"  [import-not-found]
src/agent_workbench/models/database.py:10: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.asyncio"  [import-not-found]
src/agent_workbench/models/database.py:11: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.declarative"  [import-not-found]
src/agent_workbench/models/database.py:12: error: Cannot find implementation or library stub for module named "sqlalchemy.orm"  [import-not-found]
src/agent_workbench/models/database.py:13: error: Cannot find implementation or library stub for module named "sqlalchemy.sql"  [import-not-found]
src/agent_workbench/models/database.py:14: error: Cannot find implementation or library stub for module named "sqlalchemy.dialects.postgresql"  [import-not-found]
src/agent_workbench/models/database.py:27: error: Variable "src.agent_workbench.models.database.Base" is not valid as a type  [valid-type]
src/agent_workbench/models/database.py:27: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases
src/agent_workbench/models/database.py:27: error: Invalid base class "Base"  [misc]
src/agent_workbench/models/database.py:104: error: Variable "src.agent_workbench.models.database.Base" is not valid as a type  [valid-type]
src/agent_workbench/models/database.py:104: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases
src/agent_workbench/models/database.py:104: error: Invalid base class "Base"  [misc]
src/agent_workbench/models/database.py:190: error: Variable "src.agent_workbench.models.database.Base" is not valid as a type  [valid-type]
src/agent_workbench/models/database.py:190: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases
src/agent_workbench/models/database.py:190: error: Invalid base class "Base"  [misc]
src/agent_workbench/api/routes/messages.py:6: error: Cannot find implementation or library stub for module named "fastapi"  [import-not-found]
src/agent_workbench/api/routes/messages.py:7: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.asyncio"  [import-not-found]
src/agent_workbench/api/routes/messages.py:9: error: Cannot find implementation or library stub for module named "agent_workbench.models.database"  [import-not-found]
src/agent_workbench/api/routes/messages.py:10: error: Cannot find implementation or library stub for module named "agent_workbench.models.schemas"  [import-not-found]
src/agent_workbench/api/routes/messages.py:15: error: Cannot find implementation or library stub for module named "agent_workbench.api.database"  [import-not-found]
src/agent_workbench/api/routes/messages.py:16: error: Cannot find implementation or library stub for module named "agent_workbench.api.exceptions"  [import-not-found]
src/agent_workbench/api/routes/conversations.py:6: error: Cannot find implementation or library stub for module named "fastapi"  [import-not-found]
src/agent_workbench/api/routes/conversations.py:7: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.asyncio"  [import-not-found]
src/agent_workbench/api/routes/conversations.py:9: error: Cannot find implementation or library stub for module named "agent_workbench.models.database"  [import-not-found]
src/agent_workbench/api/routes/conversations.py:10: error: Cannot find implementation or library stub for module named "agent_workbench.models.schemas"  [import-not-found]
src/agent_workbench/api/routes/conversations.py:15: error: Cannot find implementation or library stub for module named "agent_workbench.api.database"  [import-not-found]
src/agent_workbench/api/routes/conversations.py:16: error: Cannot find implementation or library stub for module named "agent_workbench.api.exceptions"  [import-not-found]
src/agent_workbench/api/routes/agent_configs.py:6: error: Cannot find implementation or library stub for module named "fastapi"  [import-not-found]
src/agent_workbench/api/routes/agent_configs.py:7: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.asyncio"  [import-not-found]
src/agent_workbench/api/routes/agent_configs.py:7: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
src/agent_workbench/api/routes/agent_configs.py:9: error: Cannot find implementation or library stub for module named "agent_workbench.models.database"  [import-not-found]
src/agent_workbench/api/routes/agent_configs.py:10: error: Cannot find implementation or library stub for module named "agent_workbench.models.schemas"  [import-not-found]
src/agent_workbench/api/routes/agent_configs.py:15: error: Cannot find implementation or library stub for module named "agent_workbench.api.database"  [import-not-found]
src/agent_workbench/api/routes/agent_configs.py:16: error: Cannot find implementation or library stub for module named "agent_workbench.api.exceptions"  [import-not-found]
src/agent_workbench/models/schemas.py:7: error: Cannot find implementation or library stub for module named "pydantic"  [import-not-found]
src/agent_workbench/api/routes/health.py:5: error: Cannot find implementation or library stub for module named "fastapi"  [import-not-found]
src/agent_workbench/api/routes/health.py:6: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.asyncio"  [import-not-found]
src/agent_workbench/api/routes/health.py:8: error: Cannot find implementation or library stub for module named "agent_workbench.models.schemas"  [import-not-found]
src/agent_workbench/api/routes/health.py:9: error: Cannot find implementation or library stub for module named "agent_workbench.api.database"  [import-not-found]
src/agent_workbench/api/database.py:6: error: Cannot find implementation or library stub for module named "sqlalchemy.ext.asyncio"  [import-not-found]
src/agent_workbench/api/database.py:7: error: Cannot find implementation or library stub for module named "sqlalchemy.orm"  [import-not-found]
src/agent_workbench/api/database.py:8: error: Cannot find implementation or library stub for module named "sqlalchemy.exc"  [import-not-found]
src/agent_workbench/api/database.py:9: error: Cannot find implementation or library stub for module named "sqlalchemy.engine"  [import-not-found]
src/agent_workbench/api/database.py:11: error: Cannot find implementation or library stub for module named "agent_workbench.models.database"  [import-not-found]
src/agent_workbench/api/database.py:12: error: Cannot find implementation or library stub for module named "agent_workbench.models.config"  [import-not-found]
src/agent_workbench/api/database.py:65: error: "None" not callable  [misc]
src/agent_workbench/api/database.py:79: error: "None" has no attribute "begin"  [attr-defined]
src/agent_workbench/api/database.py:87: error: "None" has no attribute "begin"  [attr-defined]
src/agent_workbench/api/database.py:100: error: Cannot find implementation or library stub for module named "sqlalchemy"  [import-not-found]
Found 50 errors in 11 files (checked 13 source files)
[Agent Workbench] Code quality checks complete