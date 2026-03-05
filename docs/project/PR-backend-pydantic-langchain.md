- Provide a backend assessment part 2/3: audit LangChain + Pydantic — audit providers, workflows, state models, bridge

## Why

Get a clear picture of the LangChain/Langgraph + Pydantic. Look at the Pydantic model approach and its implementation in LLM framework to understand how this model factory is treating providers, workflows, state models, bridge and other relevant artefacts. In this assessment it is also necessary to look at the broad picture. So not only rationalize, realign, and clean up, but also how do we get the fundamentals right to build from there This is the second of 3 backend assessments.

## Scope

Included:
- Pydantic models and an overlap analysis
- Implementation of Pydantic in Langchain
- Langchain concepts
- Use earlier quality scan /docs/PYDANTIC_IMPLEMENTATION_AUDIT.md
- `make db-structure` and `make code-analyze` output

Excluded:
- Gradio UI layer (assessment 3/3)
- No code changes — assessment only
- No tests needed just deliver audit report with actionable outcome.


