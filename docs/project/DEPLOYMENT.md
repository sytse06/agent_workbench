# Deployment

## Local Development

```bash
make dev        # configure environment
make start-app  # http://localhost:8000/
```

Debug modes:
```bash
make start-app-debug    # debug logging
make start-app-verbose  # max verbosity + API docs at /docs
```

## Docker

```bash
make docker-dev       # development container
make docker-staging   # staging (mirrors production)
make docker-prod      # production (main branch required)
make docker-test      # run tests in clean container
make docker-fresh     # completely clean rebuild
make docker-shell     # interactive shell in container
make docker-cleanup   # remove all agent-workbench containers/images
```

Ports: 8000 (FastAPI), 7860 (Gradio). Environment configured via `config/*.env` files passed as `--env-file`.

## HuggingFace Spaces

Auto-detected via `SPACE_ID` environment variable. Uses HubBackend (HuggingFace Datasets) instead of SQLite.

**Entry points:**
- Workbench: `deploy/hf-spaces/workbench/app.py`
- SEO Coach: `deploy/hf-spaces/seo-coach/app.py`

**Deployment:**
- Automated via GitHub Actions on push to `main` (or manual workflow_dispatch)
- Generated artifacts in `deploy/hf-spaces/`
- Environment: `config/production.env` with `APP_MODE=workbench` or `APP_MODE=seo_coach`

**Setup steps:**
1. Configure GitHub Secrets for API keys
2. Create HuggingFace Space
3. Set HF Spaces environment variables (APP_MODE, API keys)
4. Trigger GitHub Actions deployment or push to main

**Platform constraints:**
- CPU Basic tier: 16GB RAM, 8 vCPUs
- Cold start: ~45 seconds
- Persistent storage: 20GB included

## Database Migrations

```bash
uv run alembic upgrade head          # apply migrations
uv run alembic revision --autogenerate -m "description"  # generate from model changes
uv run alembic downgrade -1          # rollback one migration
uv run alembic current               # show current version
make docker-migrate                  # run migrations in container
```

Environment-specific databases:
```
data/
  agent_workbench_dev.db
  agent_workbench_staging.db
  agent_workbench_prod.db
```
