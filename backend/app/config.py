from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "E8 Compass API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    demo_fallback_enabled: bool = True
    cors_origins: str = Field(default="http://localhost:3000,https://e8.zeyu.app")

    # LLM Provider selection
    llm_provider: str = "openai"  # openai, openai_4o, openai_4, kimi, zhipu

    # OpenAI (gpt-4o-mini)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # OpenAI (gpt-4o)
    openai_4o_api_key: str = ""
    openai_4o_model: str = "gpt-4o"

    # OpenAI (gpt-4)
    openai_4_api_key: str = ""
    openai_4_model: str = "gpt-4"

    # Kimi / Moonshot
    kimi_api_key: str = ""
    kimi_model: str = "moonshot-v1-8k"

    # Gemini (Google)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Zhipu / ChatGLM
    zhipu_api_key: str = ""
    zhipu_model: str = "glm-4-flash"

    # Claude / Anthropic
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Multi-agent chain model assignments
    # Each agent can use a different provider: claude | openai | openai_4o | openai_4 | zhipu
    agent_document_reader: str = "claude"      # Claude reads documents
    agent_e8_mapper: str = "openai_4o"          # GPT-4o maps to E8 controls
    agent_evidence_checker: str = "zhipu"       # GLM-4 checks evidence quality
    agent_critic: str = "openai_4"              # GPT-4 acts as critic
    agent_guidance_writer: str = "openai"        # GPT-4o-mini writes guidance

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
