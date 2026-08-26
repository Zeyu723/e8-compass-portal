// Static demo sample — exact payload from the FastAPI /demo/sample-result endpoint
// (captured from the running backend so the demo stays faithful).
// Served by Vercel serverless so the Demo button works without the Python backend.
export const runtime = "nodejs";

const SAMPLE_RESULT = {
  assessment: {
    control: "Regular Backups",
    input_type: "Policy",
    document_scope: "Part of a document",
  },
  agent_review: [
    {
      agent: "Document Reader Agent",
      finding: "Found a weekly backup policy and IT ownership statement.",
    },
    {
      agent: "Essential Eight Mapper Agent",
      finding: "Mapped the uploaded policy to the Regular Backups control.",
    },
    {
      agent: "Evidence Checker Agent",
      finding: "Classified the input as policy-only evidence, which is weak implementation evidence.",
    },
    {
      agent: "Critic Agent",
      finding: "Restore testing, retention, backup protection, and technical evidence are missing.",
    },
    {
      agent: "Guidance Writer Agent",
      finding: "Generated assessment, gaps, clarification questions, and recommendations.",
    },
  ],
  evidence_found: [
    "Weekly backups are mentioned.",
    "IT ownership is mentioned.",
  ],
  evidence_quality: {
    evidence_type: "policy_document",
    confidence_score: 0.147,
    confidence_band: "Low",
    reason: "Policy-only evidence does not prove implementation.",
  },
  gaps: [
    {
      gap: "No restore testing evidence",
      severity: "High",
    },
    {
      gap: "No clear restore testing frequency",
      severity: "Medium",
    },
    {
      gap: "No backup retention period",
      severity: "Medium",
    },
    {
      gap: "No immutable or protected backup statement",
      severity: "High",
    },
    {
      gap: "No technical/tool output evidence",
      severity: "High",
    },
  ],
  clarification_questions: [
    "Can you provide the latest backup restore test record?",
    "What is the backup retention period?",
    "Are backups immutable or protected from unauthorised deletion?",
    "Which critical systems are covered by the backup process?",
    "Can you upload tool output proving backup configuration?",
  ],
  recommendations: [
    {
      action: "Provide or perform a backup restore test",
      priority: "High",
      reason: "Restore testing evidence is missing and this is a key assurance gap.",
    },
    {
      action: "Define backup retention period",
      priority: "Medium",
      reason: "The policy does not specify how long backups are retained.",
    },
    {
      action: "Protect backups from modification or deletion",
      priority: "High",
      reason: "The policy does not mention immutable or protected backups.",
    },
    {
      action: "Upload technical evidence such as backup tool output",
      priority: "High",
      reason: "Policy-only evidence is weak and does not prove implementation.",
    },
  ],
  final_result: {
    status: "Insufficient Evidence",
    summary: "The backup policy mentions weekly backups and IT ownership, but it does not provide restore testing evidence, retention details, backup protection controls, or technical evidence. The organisation should provide implementation evidence and strengthen the policy before this control can be assessed as compliant.",
  },
  metadata: {
    ai_mode: "fallback",
    model: "openai/gpt-4o-mini",
    used_fallback: true,
    fallback_reason: "Static demo sample",
  },
};

export async function GET() {
  return Response.json(SAMPLE_RESULT);
}
