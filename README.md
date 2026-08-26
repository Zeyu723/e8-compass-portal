# Sovereign E8 — AI-Guided Essential Eight Self-Assessment Portal

Built for **CyberWest Hackathon 2026** (WA Government security challenge, Perth) —
Team lead: Zeyu Xu, 5-person team.

**Live demo:** https://e8-compass-portal.vercel.app

An AI-assisted self-assessment portal for the ACSC **Essential Eight** maturity
model: upload policy documents, tool output, or evidence files, and a
five-agent review council reads the evidence, maps it to E8 controls, checks
what is actually proven, critiques the gaps, and writes guidance with
maturity-scored recommendations — auditable, not vague LLM output.

## Repo layout

```
├── src/                  # Next.js 16 frontend (App Router, TypeScript, Tailwind, shadcn/ui)
│   └── app/api/demo/     # serverless route serving the static demo sample
└── backend/              # FastAPI five-agent pipeline (Python)
    ├── app/services/     #   agent chain, provider routing, E8 knowledge engine, rubric
    └── tests/            #   pytest suite
```

## The five-agent pipeline

| Agent | Job |
|---|---|
| Document Reader | Extracts claims and structure from the uploaded document |
| Essential Eight Mapper | Maps extracted content to E8 controls |
| Evidence Checker | Classifies evidence strength — policy intent vs implementation proof |
| Critic | Challenges the assessment, surfaces gaps and missing evidence |
| Guidance Writer | Produces maturity rating, gaps, questions, recommendations |

A deterministic knowledge engine (`backend/app/services/e8_knowledge.py`)
encodes the Essential Eight control logic with a fixed rubric, keeping scores
consistent and auditable; LLM providers (OpenAI / Kimi / Zhipu / Claude) are
hot-swappable behind one agent interface, with rubric fallback when no
provider is reachable.

## Run

**Frontend** (deployed to Vercel):

```bash
npm install
npm run dev        # http://localhost:3000 — demo works fully offline of the backend
```

**Backend** (optional, for live assessments):

```bash
cd backend && ./run.sh    # http://localhost:8000 — see backend/README.md
```

## Status

The live portal runs frontend-only: the demo sample is served by a Vercel
serverless route, so it never depends on a separate server. The full agent
pipeline is in `backend/` for reference and local runs.

## License

MIT
