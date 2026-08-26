import json

from openai import OpenAI

from app.schemas import AgentReviewDraft, RegularBackupsAssessmentRequest
from app.services.agent_provider import AgentProvider


SYSTEM_PROMPT = """You are the multi-agent evidence review backend for E8 Compass Portal.
Review only the provided user input. Do not invent evidence.
The selected Essential Eight control is Regular Backups.
Return concise, demo-friendly JSON that matches the requested schema.
Policy statements are weak evidence and do not prove implementation."""


# Note: using json_object mode (not json_schema strict) for broader model compatibility


class BaseOpenAIProvider(AgentProvider):
    """Base class for OpenAI providers."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError(f"API key is required for OpenAI provider")
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)

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
Return JSON only.

Use this exact JSON structure:
{{
    "claims": ["..."],
    "missing_items_observed": ["..."],
    "agent_review": [{{"agent": "...", "finding": "..."}}],
    "evidence_found": ["..."],
    "clarification_questions": ["..."],
    "draft_recommendations": ["..."]
}}
"""

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = completion.choices[0].message.content or "{}"
        return AgentReviewDraft.model_validate(json.loads(content))

class OpenAIProvider(BaseOpenAIProvider):
    """OpenAI gpt-4o-mini provider."""

    pass


class OpenAI4oProvider(BaseOpenAIProvider):
    """OpenAI gpt-4o provider."""

    pass


class OpenAI4Provider(BaseOpenAIProvider):
    """OpenAI gpt-4 provider."""

    pass

