from fastapi import APIRouter

from app.config import get_settings
from app.schemas import RegularBackupsAssessmentResponse
from app.services.demo_data import SAMPLE_POLICY, sample_regular_backups_result

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/sample-policy")
def sample_policy() -> dict[str, str]:
    return {"control": "Regular Backups", "input_type": "Policy", "content": SAMPLE_POLICY}


@router.get("/sample-result", response_model=RegularBackupsAssessmentResponse)
def sample_result() -> RegularBackupsAssessmentResponse:
    settings = get_settings()
    model_name = f"{settings.llm_provider}/{settings.openai_model}"
    return sample_regular_backups_result(model=model_name, fallback_reason="Static demo sample")
