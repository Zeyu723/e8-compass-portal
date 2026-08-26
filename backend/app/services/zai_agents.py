import json

from app.schemas import AgentReviewDraft, RegularBackupsAssessmentRequest
from app.services.agent_provider import AgentProvider

# Zai (豆包) uses OpenAI-compatible API
try:
    from openai import OpenAI
except ImportError:
    raise ImportError("openai package is required for Zai provider")


SYSTEM_PROMPT = """You are the multi-agent evidence review backend for E8 Compass Portal.
Review only the provided user input. Do not invent evidence.
The selected Essential Eight control is Regular Backups.
Return concise, demo-friendly JSON that matches the requested schema.
Policy statements are weak evidence and do not prove implementation."""


def _draft_schema() -> dict:
    return AgentReviewDraft.model_json_schema()


class ZaiProvider(AgentProvider):
    """Zai (豆包 / Doubao) LLM provider."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("API key is required for Zai provider")
        self.api_key = api_key
        self.model = model
        # Zai API base: https://api.doubao.com/v1
        self.client = OpenAI(api_key=api_key, base_url="https://api.doubao.com/v1")

    def run_agent_review(self, request: RegularBackupsAssessmentRequest) -> AgentReviewDraft:
        user_prompt = f"""Assessment scope: {request.scope}
Control: {request.control}
Input type: {request.input_type}

Uploaded content:
{request.content}

Act as these agents:
1. Document Reader Agent
2. Essential Eight Mapper Agent
3. Evidence Checker Agent
4. Critic Agent
5. Guidance Writer Agent

Extract explicit claims, missing items, agent findings, evidence found, clarification questions, and draft recommendations.
Return JSON only."""

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "{}"
        return AgentReviewDraft.model_validate(json.loads(content))
