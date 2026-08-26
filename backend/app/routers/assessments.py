from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.schemas import RegularBackupsAssessmentRequest, RegularBackupsAssessmentResponse
from app.services.regular_backups import assess_regular_backups
from app.services.agent_chain import run_agent_chain_stream
from app.services.demo_data import sample_regular_backups_result
import json

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/regular-backups", response_model=RegularBackupsAssessmentResponse)
def regular_backups(request: RegularBackupsAssessmentRequest) -> RegularBackupsAssessmentResponse:
    if request.control != "Regular Backups":
        raise HTTPException(status_code=400, detail="Only Regular Backups is implemented in the MVP.")
    settings = get_settings()
    try:
        return assess_regular_backups(
            request,
            settings=settings,
            fallback_enabled=settings.demo_fallback_enabled,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Assessment failed: {type(exc).__name__}") from exc


@router.post("/regular-backups/stream")
async def regular_backups_stream(request: RegularBackupsAssessmentRequest):
    """SSE streaming endpoint — sends agent events as they complete."""
    if request.control != "Regular Backups":
        raise HTTPException(status_code=400, detail="Only Regular Backups is implemented in the MVP.")
    settings = get_settings()

    async def generate():
        try:
            async for event in run_agent_chain_stream(request, settings):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            error_event = {"type": "error", "message": f"{type(exc).__name__}: {exc}"}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
