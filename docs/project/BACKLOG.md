# Backlog

Items move from Later to Next to Now. Each "Now" item becomes a feature branch and a PR.

## Now
- [ ] Backend assessment 1/3: FastAPI + database — audit routes, models, migrations, protocol backends
- [ ] Backend assessment 2/3: LangChain + Pydantic — audit providers, workflows, state models, bridge
- [ ] Backend assessment 3/3: Gradio — audit UI components, mode factory, mounting pattern, Gradio 6 readiness

## Next
- [ ] Consolidate UI to Gradio-native styling (strip custom CSS, use standard components)
- [ ] Clean up stale remote branches (prune origin)
- [ ] Remove or archive old workflow docs (arch decisions, implementation prompts)
- [ ] Run make pre-commit and fix any quality/test issues

## Later
- [ ] Custom UI styling (Ollama-inspired) — parked on feature/ollama-ui-redesign, revisit with incremental approach (one component at a time)
- [ ] MCP tool integration (Firecrawl for SEO analysis)
- [ ] SEO Coach production deployment to HuggingFace Spaces
- [ ] Multi-agent coordination via LangGraph
- [ ] Agent memory and learning
- [ ] Context service full implementation
- [ ] File upload handling in chat interface

## Done
- [x] App running locally (make start-app, chat works, conversation history persists)
- [x] Streamlined CLAUDE.md and developer workflow
- [x] Added make pr command and PR guidelines
- [x] Created project docs (BACKLOG, DEPLOYMENT, BUSINESS)
- [x] Cleaned up 28 stale local branches
- [x] Verified HF Spaces deployment (fixed Gradio 6.x crash, switched to sdk:docker)
