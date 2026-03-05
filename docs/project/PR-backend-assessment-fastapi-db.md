| Section | What to Write |
|---|---|
| **What** | 1-2 sentences: what does this change do? |
Make an assessment of the backend by checking the 1/3: FastAPI + database implementation — audit the routes, models, migrations, protocol backends. Use the subagent code-reviewer and the make commands make db-analyze and code-analyze to do your work.
| **Why** | 1 sentence: what problem does it solve? |
We want to get a clear picture rationalize but keep pragmatic flexibility in mind so we can realign and clean up this project
| **Scope** | Bullet list: what's included. Optionally what's explicitly excluded. |
Assesment should lead to actionable list which we can bring back to the backlog
It's the first assesment in 3 steps: in other checks we will loop through langchain + pydantic and gradio implementation 
| **How to test** | How to verify it works. |
in the makefile use quality fix and make test.