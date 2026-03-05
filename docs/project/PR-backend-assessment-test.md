PR assessment test-infrastructure
| **What** | 1-2 sentences: what does this change do? |
Assess the current gradio implementation by looking at the broad picture. audit UI components, mode factory, mounting pattern, PWA implementation, Gradio 6 readiness and find concrete ways to return to gradio intrinsic styling at least for the ai-workbench
| **Why** | 1 sentence: what problem does it solve? |
We want to rationalize the ui and gradio implementation. This analysis gives us feedback on status quo and concrete steps to achieve goals
| **Scope** | Bullet list: what's included. Optionally what's explicitly excluded. |
Broad picture Gradio setup Blocks/ chat interface
Efficiency of coupling with Pydantic/Langchain and Fastapi/db backend aspects
Gradio implementation reverting styling approach
Gradio implementation on local docker, remote pwa, hf spaces
Moving to Gradio 6
| **How to test** | How to verify it works. |
Not applicable

 