from app.schemas import (
    AgentFinding,
    AssessmentContext,
    EvidenceQuality,
    FinalResult,
    Gap,
    Recommendation,
    RegularBackupsAssessmentResponse,
    ResponseMetadata,
)

SAMPLE_POLICY = """The organisation performs weekly backups of important business systems.
Backups are stored on internal infrastructure.
Restore testing may be performed when required.
The IT team is responsible for backup operations."""


def sample_regular_backups_result(model: str = "demo", fallback_reason: str | None = None) -> RegularBackupsAssessmentResponse:
    return RegularBackupsAssessmentResponse(
        assessment=AssessmentContext(
            control="Regular Backups",
            input_type="Policy",
            document_scope="Part of a document",
        ),
        agent_review=[
            AgentFinding(agent="Document Reader Agent", finding="Found a weekly backup policy and IT ownership statement."),
            AgentFinding(agent="Essential Eight Mapper Agent", finding="Mapped the uploaded policy to the Regular Backups control."),
            AgentFinding(agent="Evidence Checker Agent", finding="Classified the input as policy-only evidence, which is weak implementation evidence."),
            AgentFinding(agent="Critic Agent", finding="Restore testing, retention, backup protection, and technical evidence are missing."),
            AgentFinding(agent="Guidance Writer Agent", finding="Generated assessment, gaps, clarification questions, and recommendations."),
        ],
        evidence_found=[
            "Weekly backups are mentioned.",
            "IT ownership is mentioned.",
        ],
        evidence_quality=EvidenceQuality(
            evidence_type="policy_document",
            confidence_score=0.147,
            confidence_band="Low",
            reason="Policy-only evidence does not prove implementation.",
        ),
        gaps=[
            Gap(gap="No restore testing evidence", severity="High"),
            Gap(gap="No clear restore testing frequency", severity="Medium"),
            Gap(gap="No backup retention period", severity="Medium"),
            Gap(gap="No immutable or protected backup statement", severity="High"),
            Gap(gap="No technical/tool output evidence", severity="High"),
        ],
        clarification_questions=[
            "Can you provide the latest backup restore test record?",
            "What is the backup retention period?",
            "Are backups immutable or protected from unauthorised deletion?",
            "Which critical systems are covered by the backup process?",
            "Can you upload tool output proving backup configuration?",
        ],
        recommendations=[
            Recommendation(
                action="Provide or perform a backup restore test",
                priority="High",
                reason="Restore testing evidence is missing and this is a key assurance gap.",
            ),
            Recommendation(
                action="Define backup retention period",
                priority="Medium",
                reason="The policy does not specify how long backups are retained.",
            ),
            Recommendation(
                action="Protect backups from modification or deletion",
                priority="High",
                reason="The policy does not mention immutable or protected backups.",
            ),
            Recommendation(
                action="Upload technical evidence such as backup tool output",
                priority="High",
                reason="Policy-only evidence is weak and does not prove implementation.",
            ),
        ],
        final_result=FinalResult(
            status="Insufficient Evidence",
            summary=(
                "The backup policy mentions weekly backups and IT ownership, but it does not provide restore testing evidence, "
                "retention details, backup protection controls, or technical evidence. The organisation should provide "
                "implementation evidence and strengthen the policy before this control can be assessed as compliant."
            ),
        ),
        metadata=ResponseMetadata(
            ai_mode="fallback",
            model=model,
            used_fallback=True,
            fallback_reason=fallback_reason,
        ),
    )
