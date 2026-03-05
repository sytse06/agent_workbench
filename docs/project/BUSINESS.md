# Business Backgrounder

## What Agent Workbench Is

A LangGraph-powered platform with two operational modes serving different markets from a single codebase.

## Target Markets

### Workbench Mode (Technical)
- AI developers and researchers working with workflow orchestration
- Teams needing robust state management for multi-step AI interactions
- Language: English

### SEO Coach Mode (Business)
- Dutch small business owners (1-50 employees) seeking SEO improvement
- Marketing agencies wanting white-label SEO coaching tools
- Mobile-first AI coaching for website optimization and content strategy
- Language: Dutch

## Value Propositions

| Proposition | Detail |
|---|---|
| Dual market | One codebase, two audiences via mode switching |
| Workflow-first | All interactions through LangGraph state machines |
| Provider-agnostic | OpenRouter, Ollama, OpenAI, Anthropic via LangChain |
| Zero distribution cost | PWA on HuggingFace Spaces, no app store fees |
| Instant updates | Deploy immediately to all users |

## SEO Coach: PWA Strategy

The SEO Coach deploys as a Progressive Web App on HuggingFace Spaces.

**User experience:**
- App-like interface without App Store downloads
- Offline access to conversation history and business profiles
- Touch-friendly, mobile-optimized for smartphones/tablets
- Sub-3 second load times on mobile networks

**Business model:**
- Hosting: free tier on HuggingFace Spaces (CPU Basic)
- Distribution: zero cost (no app store fees)
- Updates: instant deployment
- Cross-platform: iOS, Android, desktop from single codebase

**Market positioning:**
- First Dutch-focused AI SEO coaching PWA
- Professional-grade tool at small business accessibility
- Zero-friction entry: no downloads, no accounts required initially

## Technical Differentiators

- LangGraph StateGraph for deterministic workflow orchestration
- Protocol-based database abstraction (SQLite local, HuggingFace Hub in Spaces)
- Gradio + FastAPI standardized mounting pattern (production-validated)
- TypedDict state models following GAIA agent patterns
- Dual-mode deployment from environment variable switching

## Phase Status

**Phase 1 (Complete):**
Core architecture, database abstraction, LangGraph workflows, dual-mode UI, Gradio+FastAPI integration, HuggingFace Spaces deployment infrastructure.

**Phase 2 (Planned):**
Active agent execution, MCP tool integration (Firecrawl for SEO), multi-agent coordination, agent memory, full context service. Not yet started.

## Success Metrics (Targets)

| Category | Metric | Target |
|---|---|---|
| Performance | Simple chat response | <3 seconds |
| Performance | Complex workflow | <10 seconds |
| Reliability | State recovery after restart | 100% |
| Reliability | Workflow failure rate | <2% |
| SEO Coach UX | Task completion rate | >90% |
| Deployment | Successful deployments | >99% |
| PWA | Mobile installation rate | >30% |
| PWA | Lighthouse PWA score | >90/100 |
