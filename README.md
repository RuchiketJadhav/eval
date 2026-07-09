# AI Voice Evaluation Platform

A polished MVP for evaluating completed AI voice-agent conversations. Users paste a transcript, click **Evaluate**, and receive an enterprise-style Quality Evaluation report powered by a single OpenAI Responses API call with Structured Outputs.

## Features

- FastAPI web application
- Jinja2 templates with TailwindCSS CDN styling
- Quality Evaluator only
- Scores for intent understanding, response correctness, context retention, conversation flow, and task completion
- Evidence-backed issues and prioritized recommendations
- JSON download and browser print support
- Pydantic v2 schemas, evaluator SDK, registry infrastructure, ruff, mypy, and pytest

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- `OPENAI_API_KEY`

## Setup

```bash
uv sync

export OPENAI_API_KEY="your-api-key"
```

Optional configuration:

```bash
export OPENAI_MODEL="gpt-5.5"
export REQUEST_TIMEOUT_SECONDS="45"
```

## Run the app

```bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`, paste a transcript, and click **Evaluate**.

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

## Project layout

```text
app/
  api/
  config/
  core/
  evaluators/
  registry/
  schemas/
  sdk/
  services/
  templates/
  utils/
tests/
docs/
```
