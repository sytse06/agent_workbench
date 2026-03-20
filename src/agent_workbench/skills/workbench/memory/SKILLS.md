---
name: memory
description: "Update long-term memory files about this user. Use when the user explicitly asks to remember something, corrects your behavior, shares important preferences, or reveals context about their project or domain. 'agents' stores behavioral notes (tone, tool habits, corrections). 'domain_context' stores project knowledge (tech stack, goals, business domain)."
---

## update
Call update_memory(key, content) to write to a memory file.

key = "agents"
  → Behavioral notes: how to work with this user.
  → Tone preferences, tool habits, explicit corrections ("stop doing X"), confirmed patterns ("yes, keep doing that").
  → Format: bullet list of concise rules, one per line.

key = "domain_context"
  → Project/domain knowledge: what you know about their work.
  → Tech stack, project goals, business profile, SEO targets, architecture decisions.
  → Format: structured markdown sections.

content = the full updated file (replace, not append)

Trigger conditions:
- User says "remember this" / "note that" / "update your notes"
- User corrects your behavior: "stop doing X", "don't Y"
- User reveals important context: tech stack, project goal, business info
- User confirms a non-obvious approach worked well
