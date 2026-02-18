# Agent Workbench

Dual-mode AI platform built on LangGraph. Run it as a developer
workbench or as a Dutch-language SEO coaching tool — same codebase,
different environment variable.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-workflow-orange)
![Gradio](https://img.shields.io/badge/Gradio-5-yellow)
![HuggingFace](https://img.shields.io/badge/HF_Spaces-deployed-green)

**Live demos:** [Workbench](https://huggingface.co/spaces/sytse06/agent-workbench-technical) · [SEO Coach](https://huggingface.co/spaces/sytse06/agent-workbench-seo-coach)

## Features

**Workbench mode**
- Multi-provider LLM support: OpenAI, Anthropic, Mistral, Gemini, Ollama
- LangGraph StateGraph workflow orchestration
- Persistent conversation storage with full state management
- Debug tools and model parameter controls

**SEO Coach mode**
- Dutch-language coaching interface
- Business profile intake → structured SEO analysis
- Same LangGraph backend, different UI persona

## Architecture

```
Gradio UI  ─→  FastAPI  ─→  LangGraph StateGraph  ─→  LLM (LangChain)
                                     ↕
                        Protocol-based DB layer
                        (SQLite local · HF Hub in Spaces)
```

## Quick start

```bash
git clone https://github.com/sytse06/agent_workbench
uv sync
make dev
make start-app                        # workbench mode
APP_MODE=seo_coach make start-app    # SEO coach mode
```

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/).

## Status

| Feature | Status |
|---|---|
| LangGraph workflow orchestration | ✅ |
| Dual-mode UI | ✅ |
| Multi-provider LLM support | ✅ |
| Persistent conversations | ✅ |
| HuggingFace Spaces deployment | ✅ |
| MCP tool integration | 🔜 Phase 2 |
| Multi-agent coordination | 🔜 Phase 2 |
