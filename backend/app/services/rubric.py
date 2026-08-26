from app.schemas import ConfidenceBand, Priority, Severity

EVIDENCE_TYPE_WEIGHTS = {
    "policy_document": 0.30,
    "manual_text": 0.30,
    "interview_claim": 0.25,
    "screenshot": 0.50,
    "exported_report": 0.70,
    "implementation_evidence_bundle": 0.88,
    "mixed_policy_and_implementation_evidence": 0.75,
    "tool_output": 0.85,
    "api_export": 0.90,
    "live_test_result": 1.00,
}


def confidence_score(evidence_type: str, freshness_score: float = 0.70, coverage_score: float = 0.70) -> float:
    weight = EVIDENCE_TYPE_WEIGHTS.get(evidence_type, EVIDENCE_TYPE_WEIGHTS["manual_text"])
    return round(weight * freshness_score * coverage_score, 3)


def confidence_band(score: float) -> ConfidenceBand:
    if score <= 0.30:
        return "Low"
    if score <= 0.60:
        return "Medium"
    if score <= 0.80:
        return "Good"
    return "Strong"


def priority_band(score: float) -> Priority:
    if score >= 0.75:
        return "High"
    if score >= 0.50:
        return "Medium"
    return "Low"


def priority_score(gap_severity: Severity, evidence_band: ConfidenceBand, control_importance: float = 0.9, ease_of_fix: float = 0.6) -> float:
    severity_values = {"High": 1.0, "Medium": 0.6, "Low": 0.3}
    weakness_values = {"Low": 1.0, "Medium": 0.6, "Good": 0.3, "Strong": 0.1}
    score = (
        0.40 * severity_values[gap_severity]
        + 0.25 * weakness_values[evidence_band]
        + 0.20 * control_importance
        + 0.15 * ease_of_fix
    )
    return round(score, 3)
