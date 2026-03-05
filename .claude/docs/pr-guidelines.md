# PR Workflow

## Before You Start

```bash
git checkout main
git pull
git checkout -b feature/short-descriptive-name
```

No arch docs, no ceremony. Just branch and build.

## While Building

Work with Claude Code on the feature branch. Commit as you go — small, logical commits. Don't batch everything into one giant commit at the end.

## Opening the PR

Use `make pr` to run checks, push, and create the PR in one command:

```bash
make pr                        # auto-fills title/body from commits
make pr BODY=path/to/desc.md   # uses your file as PR description
```

This runs the following steps:
1. Verifies you're not on `main`
2. Checks for uncommitted changes (fails if dirty)
3. Runs `make pre-commit` (quality + tests)
4. Pushes branch to origin
5. Creates PR via `gh pr create`

If you pass `BODY=`, write the file using the PR description format below. If you don't, `gh` auto-fills from your commit messages.

## PR Description

The PR description replaces architecture docs. Keep it to 5-10 lines.

| Section | What to Write |
|---|---|
| **What** | 1-2 sentences: what does this change do? |
| **Why** | 1 sentence: what problem does it solve? |
| **Scope** | Bullet list: what's included. Optionally what's explicitly excluded. |
| **How to test** | How to verify it works. |

Example:

```markdown
## What
Add chat history sidebar that loads previous conversations.

## Why
Users lose context when they refresh — need persistent history.

## Scope
- Chat history list in sidebar, ordered by date
- Click to load a previous conversation
- NOT: search, delete, or rename conversations

## How to test
make start-app -> open sidebar -> previous chats should appear
```

## Review Your Own Diff

Before merging, read the **Files Changed** tab on GitHub. Check for:

- Accidental files (.env, debug prints, leftover experiments)
- Things that don't belong in this PR (scope creep)
- Anything that makes you go "wait, why is this here?"

This takes 2-5 minutes. It's the most valuable step.

## Merging

Use **squash merge** to keep `main` clean with one commit per feature. Delete the feature branch after merge (GitHub can do this automatically).

## Full Flow

```
git checkout -b feature/my-thing     # branch
# ... build with Claude Code ...
# ... commit as you go ...
make pr BODY=notes.md                # checks + push + PR in one command
# review diff on GitHub
# squash merge + delete branch
```

No `develop` branch. No arch branches. No generated prompt docs. The PR is your documentation — it lives in git history forever, attached to the actual code changes.
