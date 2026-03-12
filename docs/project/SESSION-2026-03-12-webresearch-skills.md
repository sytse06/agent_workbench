# Session Log — WebResearch Skills Design
**Date:** 2026-03-12
**Participants:** Sytse van der Schaaf, Claude
**Type:** Design / Brainstorm — no code written
**Branch context:** `main` (PR-2.4 merged just before this session)

---

## Context

PR-2.4 (ContentRetriever Tool) landed on `main` earlier today. The agent can now
semantically retrieve content from uploaded documents via `DocumentContextGraph`. A
small housekeeping item is also pending: the `.gitignore` WAL sidecar fix
(`data/*.db-shm`, `data/*.db-wal`) was applied but not committed.

With PR-2.4 stable, this session focused entirely on the design of PR-2.5 and the
expanded skill domain vision beyond it.

---

## Topic 1: Adapting the SKILL.md Concept for a Web Runtime

### Observation

The developer surfaced the LangChain Deep Agents library and its `SKILL.md` concept as
inspiration. The key finding from examining it: Deep Agents is effectively a Claude Code
clone. It is a terminal/filesystem-aware agent. Its skills work because the agent can
read arbitrary files from disk at runtime and load their instructions dynamically.

That foundation does not exist in a web app. A Gradio/FastAPI application running in a
container has no equivalent of "read a file from the user's filesystem at inference time."

### Decision: Adapted concept, not a direct port

The team adapted the concept rather than porting it:

- `SKILLS.md` becomes a **routing artifact**, not a behavior file. Its only job is to give
  the `SkillLoader` the `name` and `description` that surface as the tool description the
  agent sees in `MessagesState`. Nothing else from `SKILLS.md` enters `MessagesState`.
- The `SKILLS.md` body (sub-skill catalog with when-to-use guidance) is loaded into
  **subgraph state** only — it is scoped to the routing decision and discarded afterward.
- All synthesis prompts and execution parameters live in Python, inside the subgraph
  implementation. No behavior is encoded in markdown files.

**Why this matters:** Progressive disclosure is preserved, but achieved differently.
In Deep Agents, the LLM reads the full skill file at runtime. Here, the LLM sees only
the tool description (from frontmatter). Full instructions never enter `MessagesState`,
keeping the outer agent's context clean.

---

## Topic 2: Hierarchical Skill Routing Architecture

### Problem

The agent will eventually have access to multiple Firecrawl capabilities: `scrape`,
`search`, `crawl`, `extract`. Exposing all four as separate tools to the outer LLM is
unreliable — similarly-described tools with overlapping use cases produce inconsistent
routing.

### Decision: Two-tier hierarchy

```
Tier 1 — Agent selects domain        (one tool per domain, coarse, non-overlapping)
Tier 2 — Subgraph selects skill      (focused LLM call against small catalog, isolated)
```

The agent makes one coarse decision: which domain tool to invoke. The subgraph handles
fine-grained skill selection internally via a dedicated `match_skill_node` — a focused LLM
call that has the full query and the sub-skill catalog, but nothing else from conversation
history.

**Why this is more reliable than flat tool exposure:** The outer agent's routing decision
is between a small number of clearly non-overlapping domains (e.g., `web_research` vs.
`document_retrieval`). The inner routing decision is made in an isolated context where the
LLM has exactly the signal it needs — the query and a small catalog — without noise from
conversation history or other tool descriptions.

### Validation from practice

The developer confirmed this reasoning from direct experience: MCP-based tools work well
in production, specifically validated with Gemini's coding tool using Firecrawl MCP. The
explicit lesson stated: **trust the LLM above deterministic routing routines**. The
reasoning capability of a sufficiently large model makes skill selection reliable even when
descriptions overlap somewhat. This gives confidence that `match_skill_node`'s LLM call
will route correctly in practice.

---

## Topic 3: SemanticRetriever as Shared Infrastructure

### Observation

After reviewing PR-2.4's `DocumentContextGraph`, the developer identified that
`WebResearchGraph` faces an identical retrieval problem. The data source differs — one
reads DB chunks from uploaded documents, the other reads Firecrawl API responses — but the
pipeline is the same: large content that needs semantic search before it can fit in a
synthesis LLM call.

The inline embedding and cosine-selection logic in `DocumentContextGraph` would need to be
duplicated verbatim in `WebResearchGraph` if not extracted.

### Decision: Extract `SemanticRetriever` in PR-2.5a before building PR-2.5b

A shared `SemanticRetriever` class encapsulates:
- `chunk_text()` — split raw text into `RetrievedChunk` objects
- `embed_chunks()` — async wrapper over `EmbeddingService.embed_batch()`
- `embed_query()` — single-query embedding
- `select()` — cosine similarity, token-budget enforcement, document-order restoration,
  fallback to `chunks[:5]` when all chunks exceed budget

PR-2.5a is a pure refactor of PR-2.4 code. No new features. `DocumentContextGraph` is
updated to use `SemanticRetriever`; all existing tests must remain green. This proves the
extraction is clean before any new code is written on top of it.

### Why keyword retrieval was explicitly rejected

TF-IDF and keyword matching handle only exact or near-exact matches. They fail on
paraphrases, synonyms, and cross-language queries. Semantic embeddings handle all of these
naturally. The developer's phrasing: "keyword search is so 2020." `all-MiniLM-L6-v2`
(already a dep from PR-2.4) is sufficient for this use case.

---

## Topic 4: Multi-Turn Caching for Web Content

### Problem

Web content fetched via Firecrawl is expensive — API credits and latency. A user
researching a site will ask multiple questions about the same content. Re-fetching on every
turn wastes both.

### Decision: Module-level cache keyed by (conversation_id, url)

Same pattern as `DocumentContextGraph`'s `_chunk_cache` and `_embedding_cache`:

```python
_web_chunk_cache: dict[str, dict[str, list[RetrievedChunk]]] = {}
_web_embedding_cache: dict[str, dict[str, list[list[float]]]] = {}
# outer key: conversation_id
# inner key: url (for scrape/crawl/extract) or normalized query string (for search)
```

Turn 1: Firecrawl fetch → chunk → embed → store in both caches.
Turn 2+: Cache hit → skip Firecrawl call and embedding entirely → retrieve semantically
against cached embeddings → synthesize.

This is the same multi-turn bug that was fixed in PR-2.4 (Gradio not sending
`conversation_id` → new UUID per turn → cache always missed). The fix is already in place
and the pattern is validated.

---

## Topic 5: Expanded Domain Vision

The session broadened scope to design a multi-domain skill architecture beyond
`web_research`. Two additional domains were fully sketched.

### data_management

Skills: `parse_file` (Excel/CSV ingestion), `ga4_query` (structured data pull),
`ga4_explore` (exploratory analysis), `transform`.

GA4 (Google Analytics 4) is treated as a first-class live data connector via the GA4
Reporting API. The developer has a background in SEO and this is a core SEO Coach use case.
Requires a service account credentials file and property ID — these are settings concerns,
not a skills concern.

### code_execution

Skills: `write_code`, `run_code`, `test_code`, `debug_code`.

The sandbox decision is explicitly deferred — `execute_node` is designed as a pluggable
boundary. Candidates discussed:

| Candidate | Tradeoff |
|---|---|
| E2B | Managed cloud sandbox, network-capable, usage cost |
| Modal | Serverless, good for data/ML workloads, latency |
| smolagents restricted interpreter | AST-based, no subprocess, zero cost, limited stdlib |

The developer built examples with HuggingFace smolagents last summer and is familiar with
its AST-based restricted Python interpreter. It is a credible option for the SEO Coach use
case (Python-scripted GA4 visualizations) where full OS access is not needed.

### The cross-domain pipeline

`data_management` → `code_execution` is the natural SEO Coach power-user pipeline:

1. GA4 query → structured dataset (1,000+ rows)
2. Python visualization script → chart

This pipeline requires data to pass between domain subgraphs. `MessagesState` cannot carry
it at scale (1,000 rows is too many tokens).

**Decision: Module-level `_data_context_cache` keyed by `conversation_id`.**

Any domain subgraph can read from and write to this shared cache. `MessagesState` sees only
a human-readable summary: "Fetched 1,247 rows from GA4 property 12345678."

### Visualization output

Explicitly marked as unsolved in the current architecture. `MessagesState` carries text
only. Options noted:

- Base64-encoded PNG embedded in a markdown image tag
- Temp file path served via a static endpoint
- Plotly JSON rendered client-side

Deferred. The serialization format does not affect the subgraph design.

### Mode-aware skill domains

```
skills/
├── shared/        web_research, data_management, code_execution
├── workbench/     (all shared domains, no additions)
└── seo_coach/     seo_analysis + (all shared domains)
```

`SkillLoader.build_tools()` receives the active mode and filters accordingly.

---

## Documents Produced This Session

| Document | Purpose |
|---|---|
| `docs/project/PR-25-webresearch-skills.md` | Full PR spec with sub-PR breakdown (2.5a, 2.5b, 2.5c), runtime flow diagram, context isolation table, file manifest, and verification checklist |
| `docs/project/BACKLOG.md` | PR-2.4 annotated with SemanticRetriever extraction note; PR-2.5 expanded with sub-PR breakdown and multi-turn cache decision |

---

## Open Items

These were raised but not decided:

| Item | Status |
|---|---|
| Sandbox choice for `code_execution` `execute_node` | Deferred — E2B vs Modal vs smolagents interpreter |
| Visualization output format for `code_execution` results | Deferred — base64 PNG, temp path, or Plotly JSON |
| `_data_context_cache` eviction policy / TTL | Deferred — module-level dict with no eviction for now |
| `.gitignore` WAL fix (`data/*.db-shm`, `data/*.db-wal`) | Pending commit — not part of this session's scope |

---

## Implementation Order

PR-2.5 is split into three sequential sub-PRs. Each is a prerequisite for the next.

```
PR-2.5a (SemanticRetriever extraction — pure refactor, no new features)
    ↓
PR-2.5b (SkillLoader + WebResearchGraph skeleton — execute_node stubbed, no Firecrawl calls)
    ↓
PR-2.5c (FirecrawlClient + wire into consolidated_service — real API calls, graceful degradation)
```

The sequencing is deliberate: 2.5a proves the extraction is clean before any new subgraph
is built on it; 2.5b proves the architecture end-to-end before any real API credentials are
required; 2.5c is the only sub-PR that requires `FIRECRAWL_API_KEY`.
