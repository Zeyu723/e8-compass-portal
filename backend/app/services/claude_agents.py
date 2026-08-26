import json
import re


try:
    import anthropic
except ImportError:
    raise ImportError("anthropic package is required for Claude provider")


SYSTEM_PROMPT = """You are the Document Reader Agent for E8 Compass Portal.
Read the uploaded policy text. Extract explicit claims only.
Do not invent evidence. Policy statements are weak evidence.
If the input is only a URL, do not claim to have read the linked document.
Return concise JSON."""


class ClaudeProvider:
    """Claude provider for Document Reader Agent."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("API key is required for Claude provider")
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    def run_document_reader(self, content: str) -> tuple[list[str], list[str]]:
        """Read document text, extract claims, and list missing items."""
        if content.strip().lower().startswith(("http://", "https://")):
            return [], [
                "External URL was submitted, but this prototype does not fetch or parse linked documents.",
                "Paste document text or upload extracted evidence for assessment.",
            ]

        prompt = f"""You are the Document Reader Agent for E8 Compass Portal, assessing the Essential Eight control "Regular Backups".

Read this policy text and:
1. Extract ALL explicit claims about backup practices.
2. Note what is MISSING - things a real backup policy should mention but does not.
3. Do not infer claims that are not explicitly written in the policy text.

Policy text:
{content}

Return ONLY this JSON:
{{"claims": ["claim 1", "claim 2"], "missing_items_observed": ["missing 1", "missing 2"]}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            data = json.loads(match.group(0)) if match else {"claims": [], "missing_items_observed": []}
        return data.get("claims", []), data.get("missing_items_observed", [])
