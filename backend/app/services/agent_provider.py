from abc import ABC, abstractmethod

from app.schemas import AgentReviewDraft, RegularBackupsAssessmentRequest


class AgentProvider(ABC):
    """Abstract base class for LLM agent providers."""

    @abstractmethod
    def run_agent_review(self, request: RegularBackupsAssessmentRequest) -> AgentReviewDraft:
        """Run multi-agent evidence review."""
        pass


def get_agent_provider(settings) -> AgentProvider:
    """Factory function to get the appropriate agent provider."""
    from app.services.kimi_agents import KimiProvider
    from app.services.openai_agents import (
        OpenAIProvider,
        OpenAI4oProvider,
        OpenAI4Provider,
    )
    from app.services.zhipu_agents import ZhipuProvider

    provider_name = settings.llm_provider.lower()

    if provider_name == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    elif provider_name == "openai_4o":
        return OpenAI4oProvider(settings.openai_4o_api_key, settings.openai_4o_model)
    elif provider_name == "openai_4":
        return OpenAI4Provider(settings.openai_4_api_key, settings.openai_4_model)
    elif provider_name == "kimi":
        return KimiProvider(settings.kimi_api_key, settings.kimi_model)
    elif provider_name == "zhipu":
        return ZhipuProvider(settings.zhipu_api_key, settings.zhipu_model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
