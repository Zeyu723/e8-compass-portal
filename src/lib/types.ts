// Types matching FastAPI backend schemas

export type AssessmentScope = "Whole document" | "Part of a document" | "Tool output" | "Evidence file";
export type EssentialEightControl =
  | "Patch Applications"
  | "Patch Operating Systems"
  | "Multi-factor Authentication"
  | "Restrict Administrative Privileges"
  | "Application Control"
  | "Restrict Microsoft Office Macros"
  | "User Application Hardening"
  | "Regular Backups";
export type InputType = "Policy" | "Text" | "Tool output" | "Evidence";
export type ConfidenceBand = "Low" | "Medium" | "Good" | "Strong";
export type Severity = "Low" | "Medium" | "High";
export type Priority = "Low" | "Medium" | "High";
export type AssessmentStatus = "Compliant" | "Partial" | "Insufficient Evidence" | "Not Compliant" | "Not Assessed";

export interface AssessmentRequest {
  scope: AssessmentScope;
  control: EssentialEightControl;
  input_type: InputType;
  content: string;
}

export interface AssessmentContext {
  control: EssentialEightControl;
  input_type: InputType;
  document_scope: AssessmentScope;
}

export interface AgentFinding {
  agent: string;
  finding: string;
}

export interface EvidenceQuality {
  evidence_type: string;
  confidence_score: number;
  confidence_band: ConfidenceBand;
  reason: string;
}

export interface Gap {
  gap: string;
  severity: Severity;
}

export interface Recommendation {
  action: string;
  priority: Priority;
  reason: string;
}

export interface FinalResult {
  status: AssessmentStatus;
  summary: string;
}

export interface ResponseMetadata {
  ai_mode: "live" | "fallback";
  model: string;
  used_fallback: boolean;
  fallback_reason: string | null;
}

export interface AssessmentResponse {
  assessment: AssessmentContext;
  agent_review: AgentFinding[];
  evidence_found: string[];
  evidence_quality: EvidenceQuality;
  gaps: Gap[];
  clarification_questions: string[];
  recommendations: Recommendation[];
  final_result: FinalResult;
  metadata: ResponseMetadata;
}
