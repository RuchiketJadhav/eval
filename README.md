# AI Voice Evaluation Platform

A production-oriented evaluation engine for completed AI voice-agent conversations.

This repository currently contains Sprint 1 — PR1 project foundation only. It provides the Python project configuration, a minimal FastAPI application, structured logging setup, and baseline test/lint/type-check tooling. Business logic and evaluators are intentionally not implemented in this PR.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Project layout

```text
app/
  api/
  core/
  sdk/
  schemas/
  registry/
  orchestrator/
  evaluators/
  reports/
  utils/
  config/
tests/
docs/
```

## Setup

```bash
uv sync
```

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

The health endpoint is available at `http://127.0.0.1:8000/health`.

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

## Docker Compose

```bash
docker compose up --build
```
