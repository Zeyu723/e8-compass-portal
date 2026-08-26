# E8 Compass Backend

FastAPI backend for the E8 Compass Portal — a five-agent pipeline that reviews
uploaded policy/evidence documents against the ACSC Essential Eight maturity
model (Regular Backups control demo).

## Architecture

- `app/routers/` — HTTP endpoints (`/health`, `/controls`, `/demo`, `/assessments`)
- `app/services/agent_chain.py` — the five-agent orchestration:
  Document Reader → Essential Eight Mapper → Evidence Checker → Critic → Guidance Writer
- `app/services/agent_provider.py` — multi-provider LLM routing (OpenAI / Kimi / Zhipu / Claude),
  each behind the same agent interface so providers swap without touching the chain
- `app/services/e8_knowledge.py` — deterministic knowledge engine encoding Essential Eight
  control logic and a fixed rubric, so scores stay auditable instead of free-form LLM output
- `app/services/rubric.py` + `regular_backups.py` — fallback scoring when no LLM is reachable
  (`DEMO_FALLBACK_ENABLED=true`)

## Run locally

```bash
./run.sh          # Linux / macOS / Git Bash
```

Windows (cmd/PowerShell) equivalent:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt anthropic
.venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
```

Then `http://localhost:8000/health`.

Copy `.env.example` to `.env` and fill in the provider key for whichever
`LLM_PROVIDER` you want (all keys are optional if `DEMO_FALLBACK_ENABLED=true`).

## Test

```bash
pytest
```

## Status

The production deployment no longer depends on this backend: the Next.js app
serves the demo sample from a serverless route (`src/app/api/demo/sample-result`).
This backend remains as the full implementation of the agent pipeline for
reference and local runs.
