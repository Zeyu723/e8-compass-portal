from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "service": "e8-compass-api", "version": settings.app_version}


@router.get("/provider")
def get_provider():
    settings = get_settings()
    provider = settings.llm_provider
    providers = {
        "openai": {"name": "OpenAI", "model": settings.openai_model, "configured": bool(settings.openai_api_key)},
        "openai_4o": {"name": "OpenAI 4o", "model": settings.openai_4o_model, "configured": bool(settings.openai_4o_api_key)},
        "openai_4": {"name": "OpenAI 4", "model": settings.openai_4_model, "configured": bool(settings.openai_4_api_key)},
        "kimi": {"name": "Kimi (Moonshot)", "model": settings.kimi_model, "configured": bool(settings.kimi_api_key)},
        "zhipu": {"name": "Zhipu (ChatGLM)", "model": settings.zhipu_model, "configured": bool(settings.zhipu_api_key)},
        "claude": {"name": "Claude (Anthropic)", "model": settings.claude_model, "configured": bool(settings.claude_api_key)},
    }
    return {
        "active_provider": provider,
        "active_model": providers.get(provider, {}).get("model", "unknown"),
        "providers": providers,
    }
