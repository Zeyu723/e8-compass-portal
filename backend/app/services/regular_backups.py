from app.schemas import (
    AssessmentContext,
    EvidenceQuality,
    FinalResult,
    Gap,
    Recommendation,
    RegularBackupsAssessmentRequest,
    RegularBackupsAssessmentResponse,
    ResponseMetadata,
)
from app.services.agent_chain import (
    _fallback_backup_claims,
    _gap_contradicted_by_content,
    _implementation_confidence_floor,
    _evidence_type_for_request,
    _questions_from_gaps,
    run_agent_chain,
)
from app.services.demo_data import sample_regular_backups_result
from app.services.rubric import confidence_band, confidence_score, priority_band, priority_score


def _detect_gaps(content: str) -> list[Gap]:
    lower = content.lower()
    gaps: list[Gap] = []
    has_restore_test = "restore test" in lower or ("restore" in lower and "frequency" in lower)
    if not has_restore_test:
        gaps.append(Gap(gap="No restore testing evidence", severity="High"))
    else:
        if "schedule" not in lower and "frequency" not in lower and "regular" not in lower:
            gaps.append(Gap(gap="No clear restore testing frequency", severity="Medium"))
    if "retention" not in lower:
        gaps.append(Gap(gap="No backup retention period", severity="Medium"))
    if not any(term in lower for term in ["immutable", "protected", "unauthorised deletion", "unauthorized deletion", "modification"]):
        gaps.append(Gap(gap="No immutable or protected backup statement", severity="High"))
    if not any(term in lower for term in ["tool output", "configuration", "export", "backup software", "backup job"]):
        gaps.append(Gap(gap="No technical/tool output evidence", severity="High"))
    if not any(term in lower for term in ["critical systems", "all systems"]):
        gaps.append(Gap(gap="No clear coverage of critical systems", severity="Medium"))
    return gaps


def _recommendations(gaps: list[Gap], evidence_band: str) -> list[Recommendation]:
    mapping = {
        "No restore testing evidence": "Provide or perform a backup restore test",
        "No clear restore testing frequency": "Define a restore testing schedule",
        "No backup retention period": "Define backup retention period",
        "No immutable or protected backup statement": "Protect backups from modification or deletion",
        "No technical/tool output evidence": "Upload technical evidence such as backup tool output",
        "No clear coverage of critical systems": "Identify critical systems covered by the backup process",
    }
    recs: list[Recommendation] = []
    for gap in gaps:
        score = priority_score(gap.severity, evidence_band)  # type: ignore[arg-type]
        recs.append(
            Recommendation(
                action=mapping.get(gap.gap, f"Address: {gap.gap}"),
                priority=priority_band(score),
                reason=f"{gap.gap} is a {gap.severity.lower()} severity gap for Regular Backups.",
            )
        )
    return recs


def _assessment_summary(evidence_found: list[str], gaps: list[Gap], recs: list[Recommendation]) -> str:
    has_external_url_notice = any("does not fetch or parse external documents" in item for item in evidence_found)
    if has_external_url_notice:
        evidence_text = "The uploaded input is an external URL rather than parsed policy or implementation evidence"
    elif evidence_found:
        evidence_text = "The uploaded evidence contains useful statements about " + ", ".join(evidence_found[:2])
    else:
        evidence_text = "The uploaded input does not contain explicit backup implementation evidence"
    gap_text = ", ".join(gap.gap.lower() for gap in gaps[:4])
    action_text = ", ".join(rec.action.rstrip(".").lower() for rec in recs[:3])

    if gap_text and action_text:
        return (
            f"{evidence_text}, but it does not provide enough implementation evidence to confirm Regular Backups compliance. "
            f"The main issues are {gap_text}. Recommended next steps are to {action_text}, and upload supporting records such as backup job exports, restore test evidence, retention settings, and access control configuration."
        )
    if gap_text:
        return (
            f"{evidence_text}, but it does not provide enough implementation evidence to confirm Regular Backups compliance. "
            f"The main issues are {gap_text}. Upload technical backup evidence, restore test records, and configuration exports to strengthen the assessment."
        )
    return (
        f"{evidence_text}. No high-priority gaps were identified from the submitted material, but technical evidence should still be retained for audit confidence."
    )


def assess_regular_backups(
    request: RegularBackupsAssessmentRequest,
    *,
    settings,
    fallback_enabled: bool,
) -> RegularBackupsAssessmentResponse:
    # Run the 5-agent multi-model chain
    try:
        draft = run_agent_chain(request, settings)
        ai_mode = "live"
        used_fallback = False
        fallback_reason = None
    except Exception as exc:
        import traceback
        traceback.print_exc()
        if fallback_enabled:
            return sample_regular_backups_result(model=f"{settings.llm_provider}/multi", fallback_reason=f"Provider error: {type(exc).__name__}: {exc}")
        raise

    # --- Evidence confidence: AI first, rubric fallback ---
    evidence_type = _evidence_type_for_request(request)
    if draft.ai_confidence is not None:
        score = draft.ai_confidence
    else:
        score = confidence_score(evidence_type)
    score = max(score, _implementation_confidence_floor(request.content))
    band = confidence_band(score)

    # --- Gaps: AI Critic Agent first, keyword fallback ---
    if draft.ai_gaps:
        gaps = []
        for g in draft.ai_gaps:
            sev = g.get("severity", "Medium")
            if sev not in ("High", "Medium", "Low"):
                sev = "Medium"
            gaps.append(Gap(
                gap=g.get("gap", "Unknown gap"),
                severity=sev,  # type: ignore[arg-type]
            ))
        gaps = [
            gap for gap in gaps
            if not _gap_contradicted_by_content(request.content, gap.gap)
        ]
    else:
        gaps = _detect_gaps(request.content)

    if not gaps:
        draft.clarification_questions = []

    # --- Recommendations: AI Guidance Agent first, rubric fallback ---
    if not gaps:
        recs = []
    elif draft.ai_recommendations:
        recs = []
        for r in draft.ai_recommendations:
            pri = r.get("priority", "Medium")
            if pri not in ("High", "Medium", "Low"):
                pri = "Medium"
            recs.append(Recommendation(
                action=r.get("action", "Unknown action"),
                priority=pri,  # type: ignore[arg-type]
                reason=r.get("reason", ""),
            ))
    else:
        recs = _recommendations(gaps, band)

    has_high_gap = any(gap.severity == "High" for gap in gaps)
    status = "Compliant" if not gaps and band in ("Good", "Strong") else ("Insufficient Evidence" if has_high_gap or band == "Low" else "Partial")

    # --- Summary: AI first, hardcoded fallback ---
    evidence_found = draft.evidence_found or draft.claims or _fallback_backup_claims(request.content)
    if not evidence_found and request.content.strip().lower().startswith(("http://", "https://")):
        evidence_found = ["A URL was submitted, but this prototype does not fetch or parse external documents."]
    summary = _assessment_summary(evidence_found, gaps, recs)

    return RegularBackupsAssessmentResponse(
        assessment=AssessmentContext(
            control=request.control,
            input_type=request.input_type,
            document_scope=request.scope,
        ),
        agent_review=draft.agent_review,
        evidence_found=evidence_found,
        evidence_quality=EvidenceQuality(
            evidence_type=evidence_type,
            confidence_score=score,
            confidence_band=band,
            reason="AI-assessed" if draft.ai_confidence else "Policy-only evidence does not prove implementation.",
        ),
        gaps=gaps,
        clarification_questions=draft.clarification_questions or _questions_from_gaps(gaps),
        recommendations=recs,
        final_result=FinalResult(
            status=status,  # type: ignore[arg-type]
            summary=summary,
        ),
        metadata=ResponseMetadata(
            ai_mode=ai_mode,
            model=f"{settings.llm_provider}/{settings.openai_model}",
            used_fallback=used_fallback,
            fallback_reason=fallback_reason,
        ),
    )
