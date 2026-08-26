from typing import Literal

from pydantic import BaseModel, Field


AssessmentScope = Literal["Whole document", "Part of a document", "Tool output", "Evidence file"]
EssentialEightControl = Literal[
    "Patch Applications",
    "Patch Operating Systems",
    "Multi-factor Authentication",
    "Restrict Administrative Privileges",
    "Application Control",
    "Restrict Microsoft Office Macros",
    "User Application Hardening",
    "Regular Backups",
]
InputType = Literal["Policy", "Text", "Tool output", "Evidence"]
ConfidenceBand = Literal["Low", "Medium", "Good", "Strong"]
Severity = Literal["Low", "Medium", "High"]
Priority = Literal["Low", "Medium", "High"]
AssessmentStatus = Literal["Compliant", "Partial", "Insufficient Evidence", "Not Compliant", "Not Assessed"]


class Control(BaseModel):
    id: str
    name: EssentialEightControl
    implemented: bool
    description: str


class RegularBackupsAssessmentRequest(BaseModel):
    scope: AssessmentScope = "Part of a document"
    control: EssentialEightControl = "Regular Backups"
    input_type: InputType = "Policy"
    content: str = Field(min_length=1, max_length=20000)


class AssessmentContext(BaseModel):
    control: EssentialEightControl
    input_type: InputType
    document_scope: AssessmentScope


class AgentFinding(BaseModel):
    agent: str
    finding: str


class EvidenceQuality(BaseModel):
    evidence_type: str
    confidence_score: float
    confidence_band: ConfidenceBand
    reason: str


class Gap(BaseModel):
    gap: str
    severity: Severity


class Recommendation(BaseModel):
    action: str
    priority: Priority
    reason: str


class FinalResult(BaseModel):
    status: AssessmentStatus
    summary: str


class ResponseMetadata(BaseModel):
    ai_mode: Literal["live", "fallback"]
    model: str
    used_fallback: bool
    fallback_reason: str | None = None


class RegularBackupsAssessmentResponse(BaseModel):
    assessment: AssessmentContext
    agent_review: list[AgentFinding]
    evidence_found: list[str]
    evidence_quality: EvidenceQuality
    gaps: list[Gap]
    clarification_questions: list[str]
    recommendations: list[Recommendation]
    final_result: FinalResult
    metadata: ResponseMetadata


class AgentReviewDraft(BaseModel):
    claims: list[str] = []
    missing_items_observed: list[str] = []
    agent_review: list[AgentFinding] = []
    evidence_found: list[str] = []
    clarification_questions: list[str] = []
    draft_recommendations: list[str] = []

    # AI-structured data from agents (primary); keyword-based is fallback
    maturity_assessed: str | None = None       # e.g. "ML0" from Agent 2
    ai_confidence: float | None = None          # from Agent 3
    ai_gaps: list[dict] = []                     # [{"gap":"...","severity":"High","evidence":"..."}] from Agent 4
    ai_recommendations: list[dict] = []          # [{"action":"...","priority":"High","reason":"..."}] from Agent 5
