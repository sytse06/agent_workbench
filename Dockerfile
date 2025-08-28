# Multi-stage Docker build for Agent Workbench with UV

# Build stage
FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files and source code
COPY pyproject.toml .
COPY src/ ./src/

# Install dependencies with UV (this will also build the local package)
RUN uv sync --no-dev

# Runtime stage
FROM python:3.10-slim-bookworm AS runtime

WORKDIR /app

# Install UV in runtime stage too
RUN pip install uv

# Copy UV and dependencies from builder
COPY --from=builder /app/.venv ./.venv

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Create data directory for SQLite
RUN mkdir -p data

# Expose FastAPI port
EXPOSE 8000

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"

# Run FastAPI application
CMD ["uv", "run", "python", "-m", "agent_workbench"]