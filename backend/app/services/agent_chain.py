"""Multi-Agent Chain Orchestrator.
Runs 5 agents sequentially, each with its own LLM provider.
"""

import json
import re
from openai import OpenAI

from app.schemas import AgentFinding, AgentReviewDraft, RegularBackupsAssessmentRequest
from app.services.claude_agents import ClaudeProvider
from app.services.e8_knowledge import E8_KNOWLEDGE


AGENT_NAMES = [
    "Document Reader Agent",
    "Essential Eight Mapper Agent",
    "Evidence Checker Agent",
    "Critic Agent",
    "Guidance Writer Agent",
]


def run_agent_chain(request: RegularBackupsAssessmentRequest, settings) -> AgentReviewDraft:
    """Run 5 agents in sequence, each with different provider/model."""

    agent_review: list[AgentFinding] = []
    all_claims: list[str] = []
    all_missing: list[str] = []
    all_evidence: list[str] = []
    all_questions: list[str] = []
    all_recs: list[str] = []
    maturity_assessed = None
    ai_confidence = None
    ai_gaps: list[dict] = []
    ai_recs: list[dict] = []
    context = f"\n[ASSESSMENT CONTEXT]\n{_assessment_context(request)}\n"

    # === Agent 1: Document Reader (Claude) ===
    claude = ClaudeProvider(settings.claude_api_key, settings.claude_model)
    claims, missing = claude.run_document_reader(request.content)
    if not claims:
        claims = _fallback_backup_claims(request.content)
    agent_review.append(AgentFinding(
        agent="Document Reader Agent",
        finding=f"Found {len(claims)} claims in the document. Identified {len(missing)} missing items for Regular Backups assessment."
    ))
    all_claims = claims
    all_missing = missing
    context += f"\n[DOCUMENT READER]\nClaims: {json.dumps(claims)}\nMissing: {json.dumps(missing)}\n"

    # === Agent 2: E8 Mapper (GPT-4o) ===
    e8_raw = _call_openai_agent(
        settings.openai_4o_api_key, settings.openai_4o_model,
        "Essential Eight Mapper Agent",
        f"""Map the following claims to the Essential Eight "Regular Backups" control.
{context}
Original policy excerpt:
{_content_excerpt(request.content)}

Determine which ASD maturity level (ML0, ML1, ML2, or ML3) the evidence supports, and list specific requirements that are met vs unmet.
Return a JSON:
{{
  "finding": "your analysis",
  "maturity_assessed": "ML0",
  "met_requirements": ["requirement met 1"],
  "unmet_requirements": ["requirement not met 1", "requirement not met 2"]
}}"""
    )
    e8_finding = _extract_finding(e8_raw)
    try:
        e8_display_data = _load_agent_json(e8_raw)
        e8_finding = _format_mapper_finding(e8_display_data)
    except ValueError:
        pass
    agent_review.append(AgentFinding(agent="Essential Eight Mapper Agent", finding=e8_finding))
    context += f"\n[E8 MAPPER]\n{e8_finding}\n"
    # Parse structured data
    maturity_assessed = None
    try:
        e8_data = _load_agent_json(e8_raw)
        maturity_assessed = e8_data.get("maturity_assessed")
    except ValueError:
        pass

    # === Agent 3: Evidence Checker (Zhipu/GLM-4) ===
    evidence_raw = _call_openai_agent(
        settings.openai_4o_api_key, settings.openai_4o_model,
        "Evidence Checker Agent",
        f"""Evaluate the evidence quality.
{context}
Original input type: {request.input_type}
Original policy excerpt:
{_content_excerpt(request.content)}

Classify evidence type, strength, and assign a confidence score (0.0-1.0). Policy-only is weak (<=0.3). Tool output is strong (>=0.7).
Return a JSON:
{{
  "finding": "your analysis",
  "evidence_type": "{_evidence_type_for_request(request)}",
  "strength": "weak",
  "confidence": 0.15,
  "reason": "why this score"
}}""",
    )
    evidence_finding = _extract_finding(evidence_raw)
    # Parse structured confidence
    ai_confidence = None
    try:
        ev_data = _load_agent_json(evidence_raw)
        ev_data = _apply_evidence_heuristics(request, ev_data)
        ai_confidence = ev_data.get("confidence")
        evidence_finding = _format_evidence_finding(ev_data)
    except ValueError:
        pass
    agent_review.append(AgentFinding(agent="Evidence Checker Agent", finding=evidence_finding))
    context += f"\n[EVIDENCE CHECKER]\n{evidence_finding}\n"

    # === Agent 4: Critic (GPT-4o for faster long-evidence demo runs) ===
    critic_raw = _call_openai_agent(
        settings.openai_4o_api_key, settings.openai_4o_model,
        "Critic Agent",
        f"""Challenge weak assumptions and identify all gaps.
{context}
Original policy excerpt:
{_content_excerpt(request.content)}

Return concise valid JSON only. For each gap, specify what is missing, its severity (High/Medium/Low), and cite the specific evidence from the policy that proves the gap exists. Limit to 8 gaps and 8 questions.
Return a JSON:
{{
  "finding": "your analysis",
  "gaps": [
    {{"gap": "No restore testing schedule", "severity": "High", "evidence": "Restore testing may be performed when required"}}
  ],
  "questions": ["question 1", "question 2"]
}}""",
        max_tokens=1800,
    )
    critic_finding = _extract_finding(critic_raw)
    # Parse structured gaps and questions
    ai_gaps: list[dict] = []
    try:
        cr_data = _load_agent_json(critic_raw)
        cr_data = _filter_critic_data(request.content, cr_data)
        all_questions = cr_data.get("questions", [])
        ai_gaps = cr_data.get("gaps", [])
        critic_finding = _format_critic_finding(cr_data)
    except ValueError:
        all_questions = []
    agent_review.append(AgentFinding(agent="Critic Agent", finding=critic_finding))
    context += f"\n[CRITIC]\n{critic_finding}\n"

    # === Agent 5: Guidance Writer (GPT-4o-mini) ===
    guidance_raw = _call_openai_agent(
        settings.openai_api_key, settings.openai_model,
        "Guidance Writer Agent",
        f"""Generate final assessment with concrete, evidence-based recommendations.
{context}
Original policy excerpt:
{_content_excerpt(request.content)}

Generate one recommendation for each high or medium gap, capped at 6 recommendations.
Each recommendation must have an action, priority (High/Medium/Low), and a reason that references the observed gap and suggested evidence to upload.
Return a JSON:
{{
  "finding": "summary of your guidance",
  "evidence_found": ["item 1", "item 2"],
  "recommendations": [
    {{"action": "Define restore testing schedule", "priority": "High", "reason": "Policy says testing 'may be performed when required' with no schedule; upload restore test records or a testing calendar"}}
  ],
  "clarification_questions": ["q1", "q2"],
  "summary": "two sentence final summary"
}}"""
    )
    guidance_finding = _extract_finding(guidance_raw)
    agent_review.append(AgentFinding(agent="Guidance Writer Agent", finding=guidance_finding))
    # Parse structured recommendations
    ai_recs: list[dict] = []
    final_summary = ""
    try:
        gw_data = _load_agent_json(guidance_raw)
        all_evidence = gw_data.get("evidence_found", all_claims)
        ai_recs = gw_data.get("recommendations", [])
        all_recs = [
            r.get("action", "") if isinstance(r, dict) else str(r)
            for r in ai_recs
        ]
        final_summary = gw_data.get("summary", "")
    except ValueError:
        all_evidence = all_claims

    return AgentReviewDraft(
        claims=all_claims,
        missing_items_observed=all_missing,
        agent_review=agent_review,
        evidence_found=all_evidence,
        clarification_questions=all_questions,
        draft_recommendations=all_recs,
        maturity_assessed=maturity_assessed,
        ai_confidence=ai_confidence,
        ai_gaps=ai_gaps,
        ai_recommendations=ai_recs,
    )


async def run_agent_chain_stream(request: RegularBackupsAssessmentRequest, settings):
    """Async generator: yields SSE events as each agent completes."""
    import asyncio
    all_questions = []
    ai_gaps = []
    ai_recs = []
    ai_confidence = None
    context = f"\n[ASSESSMENT CONTEXT]\n{_assessment_context(request)}\n"

    # Agent 1: Document Reader (Claude)
    yield {"type": "agent_start", "agent": "Document Reader Agent", "model": settings.claude_model}
    claude = ClaudeProvider(settings.claude_api_key, settings.claude_model)
    claims, missing = await asyncio.to_thread(claude.run_document_reader, request.content)
    if not claims:
        claims = _fallback_backup_claims(request.content)
    finding1 = f"Found {len(claims)} claims in the document. Identified {len(missing)} missing items for Regular Backups assessment."
    yield {"type": "agent_done", "agent": "Document Reader Agent", "finding": finding1}
    context += f"\n[DOCUMENT READER]\nClaims: {json.dumps(claims)}\nMissing: {json.dumps(missing)}\n"

    # Agent 2: E8 Mapper (GPT-4o)
    yield {"type": "agent_start", "agent": "Essential Eight Mapper Agent", "model": settings.openai_4o_model}
    e8_raw = await asyncio.to_thread(_call_openai_agent, settings.openai_4o_api_key, settings.openai_4o_model, "Essential Eight Mapper Agent", f"""Map claims to Regular Backups.
{context}
Policy excerpt:
{_content_excerpt(request.content)}

Determine which ASD maturity level (ML0, ML1, ML2, or ML3) the evidence supports. Return JSON:
{{
  "finding": "concise analysis",
  "maturity_assessed": "ML0",
  "met_requirements": ["requirement met 1"],
  "unmet_requirements": ["requirement not met 1"]
}}""")
    e8_finding = _extract_finding(e8_raw)
    try:
        e8_display_data = _load_agent_json(e8_raw)
        e8_finding = _format_mapper_finding(e8_display_data)
    except ValueError:
        pass
    yield {"type": "agent_done", "agent": "Essential Eight Mapper Agent", "finding": e8_finding}
    context += f"\n[E8 MAPPER]\n{e8_finding}\n"

    # Agent 3: Evidence Checker (Zhipu)
    yield {"type": "agent_start", "agent": "Evidence Checker Agent", "model": settings.openai_4o_model}
    ev_raw = await asyncio.to_thread(_call_openai_agent, settings.openai_4o_api_key, settings.openai_4o_model, "Evidence Checker Agent", f"""Evaluate evidence quality.
{context}
Type: {request.input_type}
Original policy excerpt:
{_content_excerpt(request.content)}

Classify evidence type, strength, and confidence. Policy-only is weak (<=0.3). Tool output is strong (>=0.7). Return JSON:
{{
  "finding": "concise analysis",
  "evidence_type": "{_evidence_type_for_request(request)}",
  "strength": "weak",
  "confidence": 0.15,
  "reason": "why this score"
}}""")
    ev_finding = _extract_finding(ev_raw)
    try:
        ev_data = _load_agent_json(ev_raw)
        ev_data = _apply_evidence_heuristics(request, ev_data)
        ai_confidence = ev_data.get("confidence")
        ev_finding = _format_evidence_finding(ev_data)
    except ValueError:
        ai_confidence = None
    yield {"type": "agent_done", "agent": "Evidence Checker Agent", "finding": ev_finding}
    context += f"\n[EVIDENCE CHECKER]\n{ev_finding}\n"

    # Agent 4: Critic (GPT-4o for faster long-evidence demo runs)
    yield {"type": "agent_start", "agent": "Critic Agent", "model": settings.openai_4o_model}
    cr_raw = await asyncio.to_thread(_call_openai_agent, settings.openai_4o_api_key, settings.openai_4o_model, "Critic Agent", f"""Challenge weak assumptions and identify all gaps.
{context}
Original policy excerpt:
{_content_excerpt(request.content)}

Return concise valid JSON only. For each gap, specify what is missing, its severity (High/Medium/Low), and cite the specific evidence. Limit to 8 gaps and 8 questions.
Return a JSON:
{{
  "finding": "your analysis",
  "gaps": [
    {{"gap": "No restore testing schedule", "severity": "High", "evidence": "Restore testing may be performed when required"}}
  ],
  "questions": ["question 1", "question 2"]
}}""", None, 1800)
    cr_finding = _extract_finding(cr_raw)
    # Parse structured gaps and questions
    ai_gaps = []
    try:
        cr_data = _load_agent_json(cr_raw)
        cr_data = _filter_critic_data(request.content, cr_data)
        all_questions = cr_data.get("questions", [])
        ai_gaps = cr_data.get("gaps", [])
        cr_finding = _format_critic_finding(cr_data)
    except ValueError:
        all_questions = []
    yield {"type": "agent_done", "agent": "Critic Agent", "finding": cr_finding}
    context += f"\n[CRITIC]\n{cr_finding}\n"

    # Agent 5: Guidance Writer (GPT-4o-mini)
    yield {"type": "agent_start", "agent": "Guidance Writer Agent", "model": settings.openai_model}
    gw_raw = await asyncio.to_thread(_call_openai_agent, settings.openai_api_key, settings.openai_model, "Guidance Writer Agent", f"""Based on the full analysis above, write a one-sentence compliance verdict and generate one recommendation for each high or medium gap, capped at 6 recommendations.
{context}
Original policy excerpt:
{_content_excerpt(request.content)}

Be concise. Each recommendation must reference a specific observed gap and mention the evidence that would close it.
Return JSON:
{{
  "finding": "one sentence verdict",
  "evidence_found": ["item 1"],
  "recommendations": [
    {{"action": "short action", "priority": "High", "reason": "one sentence why, including suggested evidence to upload"}}
  ],
  "clarification_questions": ["q1"],
  "summary": "two sentence final summary"
}}""", None, 1400)
    gw_finding = _extract_finding(gw_raw)
    try:
        gw_data = _load_agent_json(gw_raw)
        ai_recs = gw_data.get("recommendations", [])
    except ValueError:
        pass
    yield {"type": "agent_done", "agent": "Guidance Writer Agent", "finding": gw_finding}

    # Build final result from stream data
    from app.schemas import (
        AgentFinding, AssessmentContext, EvidenceQuality, FinalResult, Gap, Recommendation,
        RegularBackupsAssessmentResponse, ResponseMetadata,
    )
    from app.services.regular_backups import _assessment_summary, _detect_gaps, _recommendations
    from app.services.rubric import confidence_band, confidence_score

    stream_agent_review = [
        AgentFinding(agent="Document Reader Agent", finding=f"Found {len(claims)} claims. Identified {len(missing)} missing items."),
        AgentFinding(agent="Essential Eight Mapper Agent", finding=e8_finding),
        AgentFinding(agent="Evidence Checker Agent", finding=ev_finding),
        AgentFinding(agent="Critic Agent", finding=cr_finding),
        AgentFinding(agent="Guidance Writer Agent", finding=gw_finding),
    ]
    stream_evidence = list(claims)
    if not stream_evidence and request.content.strip().lower().startswith(("http://", "https://")):
        stream_evidence = ["A URL was submitted, but this prototype does not fetch or parse external documents."]

    evidence_type = _evidence_type_for_request(request)
    score = ai_confidence if ai_confidence is not None else confidence_score(evidence_type)
    score = max(score, _implementation_confidence_floor(request.content))
    band = confidence_band(score)

    gaps = []
    if ai_gaps:
        for g in ai_gaps:
            if isinstance(g, dict):
                sev = g.get("severity", "Medium")
                if sev not in ("High", "Medium", "Low"): sev = "Medium"
                gap_text = g.get("gap", "Unknown")
                if not _gap_contradicted_by_content(request.content, gap_text):
                    gaps.append(Gap(gap=gap_text, severity=sev))
            elif isinstance(g, str):
                if not _gap_contradicted_by_content(request.content, g):
                    gaps.append(Gap(gap=g, severity="Medium"))
    else:
        gaps = _detect_gaps(request.content)

    if not gaps:
        all_questions = []
    if not all_questions:
        all_questions = _questions_from_gaps(gaps)

    recs = []
    if not gaps:
        recs = []
    elif ai_recs:
        for r in ai_recs:
            if isinstance(r, dict):
                pri = r.get("priority", "Medium")
                if pri not in ("High", "Medium", "Low"): pri = "Medium"
                recs.append(Recommendation(action=r.get("action", ""), priority=pri, reason=r.get("reason", "")))
    else:
        recs = _recommendations(gaps, band)

    has_high = any(g.severity == "High" for g in gaps)
    status = "Compliant" if not gaps and band in ("Good", "Strong") else ("Insufficient Evidence" if has_high or band == "Low" else "Partial")

    result = RegularBackupsAssessmentResponse(
        assessment=AssessmentContext(control=request.control, input_type=request.input_type, document_scope=request.scope),
        agent_review=stream_agent_review,
        evidence_found=stream_evidence,
        evidence_quality=EvidenceQuality(evidence_type=evidence_type, confidence_score=score, confidence_band=band, reason="AI-assessed" if ai_confidence is not None else "Policy-only evidence does not prove implementation."),
        gaps=gaps,
        clarification_questions=all_questions,
        recommendations=recs,
        final_result=FinalResult(status=status, summary=_assessment_summary(stream_evidence, gaps, recs)),
        metadata=ResponseMetadata(ai_mode="live", model=f"{settings.llm_provider}/multi", used_fallback=False, fallback_reason=None),
    )
    yield {"type": "done", "result": result.model_dump()}


def _extract_finding(json_str: str) -> str:
    """Extract finding text from agent JSON, or return plain text."""
    try:
        data = _load_agent_json(json_str)
        if not isinstance(data, dict):
            return json_str
        # Standard format: {"finding": "text"}
        if "finding" in data:
            val = data["finding"]
            if isinstance(val, str):
                return val
            if isinstance(val, dict):
                # {"finding": {"maturity_level": ..., "analysis": [...]}}
                parts = []
                if "maturity_level" in val:
                    parts.append(f"Maturity: {val['maturity_level']}")
                if "analysis" in val and isinstance(val["analysis"], list):
                    parts.append("; ".join(val["analysis"]))
                return ". ".join(parts) if parts else json.dumps(val)
            return str(val)
        # Non-standard: {"maturity_level": ..., "analysis": [...]}
        parts = []
        if "maturity_level" in data:
            parts.append(f"Maturity: {data['maturity_level']}")
        if "analysis" in data and isinstance(data["analysis"], list):
            parts.append("; ".join(data["analysis"]))
        if parts:
            return ". ".join(parts)
        # Last resort: return the text prettily
        return json.dumps(data, indent=2)
    except (ValueError, TypeError):
        match = re.search(r'"finding"\s*:\s*"([^"]+)', json_str, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
        if json_str.strip().startswith("{"):
            return "Structured analysis was generated, but the response was not valid JSON."
        return json_str


def _assessment_context(request: RegularBackupsAssessmentRequest) -> str:
    scope_notes = {
        "Whole document": "Treat this as a broad document review. Look for coverage, exclusions, limitations, and multiple evidence sections.",
        "Part of a document": "Treat this as a limited excerpt. Do not infer evidence outside the provided text.",
        "Tool output": "Treat this as possible implementation evidence. Look for concrete logs, configuration, timestamps, system names, and results.",
        "Evidence file": "Treat this as supporting evidence. Check provenance, date, scope, and whether it proves implementation.",
    }
    input_notes = {
        "Policy": "Policy-only evidence is weak: it can show intent but not implementation.",
        "Text": "Manual text is weak to medium depending on specificity and whether it includes verifiable details.",
        "Tool output": "Tool output can be strong when it includes configuration, logs, test results, timestamps, and system scope.",
        "Evidence": "Evidence can be stronger when it is dated, scoped, and tied to real systems or control operation.",
    }
    return (
        f"Scope: {request.scope}. {scope_notes.get(request.scope, '')}\n"
        f"Input type: {request.input_type}. {input_notes.get(request.input_type, '')}\n"
        "Evidence strength must be based on the content itself, not the file extension or selected button alone."
    )


def _evidence_type_for_request(request: RegularBackupsAssessmentRequest) -> str:
    if request.content.strip().lower().startswith(("http://", "https://")):
        return "external_url_reference"
    signal_count = _implementation_signal_count(request.content)
    if signal_count >= 7:
        return "implementation_evidence_bundle"
    if signal_count >= 4:
        return "mixed_policy_and_implementation_evidence"
    if request.input_type == "Tool output" or request.scope == "Tool output":
        return "tool_output"
    if request.input_type == "Evidence" or request.scope == "Evidence file":
        return "exported_report"
    if request.input_type == "Policy":
        return "policy_document"
    return "manual_text"


def _content_excerpt(content: str, max_chars: int = 6000) -> str:
    """Keep later-agent prompts fast while preserving evidence from both ends."""
    text = content.strip()
    if len(text) <= max_chars:
        return text
    head_len = max_chars // 2
    tail_len = max_chars - head_len
    head = text[:head_len].rstrip()
    tail = text[-tail_len:].lstrip()
    return (
        f"{head}\n\n"
        f"[Content truncated for agent context: original length {len(text)} characters. "
        "Middle omitted. Use Document Reader claims and missing items as the primary evidence summary.]\n\n"
        f"{tail}"
    )


def _implementation_signal_count(content: str) -> int:
    lower = content.lower()
    signal_groups = [
        ("backup tool", ["veeam", "commvault", "rubrik", "cohesity", "backup & replication", "backup job"]),
        ("job result", ["status: success", "result: success", "completed 2026", "restore points available", "job:"]),
        ("retention", ["retention", "daily backups:", "weekly backups:", "monthly backups:", "yearly backups:"]),
        ("restore testing", ["restore test", "restore testing", "restore point", "mailbox recovery", "full vm restore", "checksum verified"]),
        ("scope", ["systems in scope", "tier 1", "tier 2", "prod-sql", "domain controllers"]),
        ("offsite storage", ["offsite", "cloud connect", "geographically separated", "data centre", "data center"]),
        ("encryption", ["aes-256", "tls 1.3", "encrypted at rest", "in-transit encryption"]),
        ("access control", ["access controls", "role assignments", "backup administrators", "read-only", "mfa enabled"]),
        ("immutability", ["immutable", "cannot delete", "cannot modify", "protected from", "air-gapped"]),
        ("monitoring", ["monitoring", "alerting", "veeam one", "servicenow", "dashboard reviewed"]),
    ]
    return sum(1 for _, terms in signal_groups if any(term in lower for term in terms))


def _implementation_confidence_floor(content: str) -> float:
    signal_count = _implementation_signal_count(content)
    if signal_count >= 8:
        return 0.82
    if signal_count >= 6:
        return 0.72
    if signal_count >= 4:
        return 0.55
    return 0.0


def _fallback_backup_claims(content: str) -> list[str]:
    lower = content.lower()
    candidates = [
        ("Backups are performed on a defined schedule.", ["daily", "incremental", "weekly full"]),
        ("Critical and important systems are listed in scope.", ["systems in scope", "tier 1", "tier 2"]),
        ("Backup retention periods are documented.", ["retention", "30 days", "90 days", "12 months", "7 years"]),
        ("Backups are encrypted in storage and transit.", ["aes-256", "tls 1.3", "encrypted at rest"]),
        ("Restore testing records or schedules are provided.", ["restore test", "restore testing", "restore point", "result: success"]),
        ("Backup job output includes status, timestamps, and restore points.", ["job:", "status: success", "restore points available"]),
        ("Access to backup administration is restricted.", ["backup administrators", "role assignments", "mfa enabled"]),
        ("Backups are protected or immutable.", ["immutable", "cannot delete", "air-gapped"]),
        ("Backup monitoring and alerting are described.", ["monitoring", "alerting", "servicenow", "dashboard reviewed"]),
        ("Offsite or geographically separated backup storage is described.", ["offsite", "cloud connect", "geographically separated"]),
    ]
    claims = []
    for claim, terms in candidates:
        if any(term in lower for term in terms):
            claims.append(claim)
    return claims


def _gap_contradicted_by_content(content: str, gap: str) -> bool:
    lower = content.lower()
    gap_lower = gap.lower()
    checks = [
        (["job execution", "backup execution", "backup job", "success"], ["status: success", "job:", "restore points available"]),
        (["immutable"], ["immutable", "cannot delete", "cannot modify"]),
        (["access control", "access"], ["backup administrators", "role assignments", "mfa enabled", "read-only"]),
        (["encryption"], ["aes-256", "tls 1.3", "encrypted at rest"]),
        (["monitoring", "alerting"], ["monitoring", "alerting", "veeam one", "servicenow"]),
        (["retention"], ["retention", "30 days", "90 days", "12 months", "7 years"]),
        (["restore", "testing"], ["restore test", "restore testing", "result: success", "checksum verified"]),
        (["air-gapped", "air gapped"], ["air-gapped", "dedicated vlan"]),
        (["offsite", "storage"], ["offsite", "cloud connect", "geographically separated"]),
        (["tier 3", "lower systems", "coverage"], ["tier 3", "development", "weekly full backup"]),
        (["integrity", "verification"], ["surebackup", "checksum verified", "sha-256 checksum"]),
    ]
    for gap_terms, evidence_terms in checks:
        if any(term in gap_lower for term in gap_terms) and any(term in lower for term in evidence_terms):
            return True
    return False


def _apply_evidence_heuristics(request: RegularBackupsAssessmentRequest, data: dict) -> dict:
    heuristic_type = _evidence_type_for_request(request)
    floor = _implementation_confidence_floor(request.content)
    if heuristic_type not in ("implementation_evidence_bundle", "mixed_policy_and_implementation_evidence"):
        return data

    adjusted = dict(data)
    adjusted["evidence_type"] = heuristic_type
    current_confidence = adjusted.get("confidence")
    if not isinstance(current_confidence, (int, float)):
        current_confidence = 0.0
    adjusted["confidence"] = max(float(current_confidence), floor)
    adjusted["strength"] = "strong" if adjusted["confidence"] >= 0.8 else "good"
    adjusted["reason"] = (
        "The content contains implementation-specific backup evidence such as tool/job output, "
        "restore testing records, retention settings, access controls, encryption, monitoring, "
        "and immutable or protected backup storage. The selected input button alone should not "
        "downgrade this evidence to policy-only."
    )
    return adjusted


def _filter_critic_data(content: str, data: dict) -> dict:
    gaps = data.get("gaps")
    if not isinstance(gaps, list):
        return data

    filtered_gaps = []
    for gap in gaps:
        gap_text = gap.get("gap", "") if isinstance(gap, dict) else str(gap)
        if not _gap_contradicted_by_content(content, gap_text):
            filtered_gaps.append(gap)

    adjusted = dict(data)
    adjusted["gaps"] = filtered_gaps
    if not filtered_gaps:
        adjusted["questions"] = []
        adjusted["finding"] = (
            "The critic found no major remaining evidence gaps after checking the provided "
            "implementation details against backup requirements."
        )
    else:
        questions = data.get("questions")
        adjusted["questions"] = questions[: len(filtered_gaps)] if isinstance(questions, list) else []
    return adjusted


def _format_mapper_finding(data: dict) -> str:
    maturity = data.get("maturity_assessed") or data.get("maturity_level") or "ML0"
    met = data.get("met_requirements") or []
    unmet = data.get("unmet_requirements") or []
    met_count = len(met) if isinstance(met, list) else 0
    unmet_count = len(unmet) if isinstance(unmet, list) else 0
    if unmet_count:
        preview = "; ".join(str(item) for item in unmet[:2])
        return f"Mapped evidence to Regular Backups at {maturity}. Met requirements: {met_count}; unmet or unevidenced requirements: {unmet_count}. Key missing requirements: {preview}."
    return f"Mapped evidence to Regular Backups at {maturity}. Met requirements: {met_count}; no major unmet requirements were returned by the mapper."


def _format_evidence_finding(data: dict) -> str:
    evidence_type = data.get("evidence_type", "unknown evidence")
    strength = data.get("strength", "unknown")
    confidence = data.get("confidence")
    reason = str(data.get("reason") or data.get("finding") or "").strip()
    prefix = f"Classified the input as {evidence_type} with {strength} evidence strength"
    if confidence is not None:
        prefix += f" and confidence {confidence}"
    if reason:
        return f"{prefix}. {reason}"
    return f"{prefix}. Policy-only evidence can show intent but does not prove implementation."


def _format_critic_finding(data: dict) -> str:
    gaps = data.get("gaps") or []
    questions = data.get("questions") or []
    if isinstance(gaps, list) and gaps:
        high_count = sum(1 for gap in gaps if isinstance(gap, dict) and gap.get("severity") == "High")
        top_gaps = []
        for gap in gaps[:3]:
            top_gaps.append(gap.get("gap", "Unknown gap") if isinstance(gap, dict) else str(gap))
        return f"Identified {len(gaps)} evidence gaps, including {high_count} high-severity gaps. Top gaps: {'; '.join(top_gaps)}. Generated {len(questions) if isinstance(questions, list) else 0} clarification questions."
    finding = data.get("finding")
    return str(finding) if finding else "Reviewed assumptions and identified no structured gaps."


def _questions_from_gaps(gaps) -> list[str]:
    """Generate deterministic clarification questions when AI question JSON fails."""
    questions: list[str] = []
    for gap in gaps[:8]:
        gap_text = getattr(gap, "gap", str(gap)).lower()
        if "retention" in gap_text:
            questions.append("What is the backup retention period or schedule?")
        elif "restore" in gap_text:
            questions.append("Can you provide the latest restore test record and testing schedule?")
        elif "immutable" in gap_text or "protected" in gap_text or "delete" in gap_text:
            questions.append("How are backups protected from modification or deletion?")
        elif "technical" in gap_text or "tool" in gap_text or "configuration" in gap_text:
            questions.append("Can you upload backup tool output or configuration evidence?")
        elif "critical" in gap_text or "coverage" in gap_text:
            questions.append("Which critical systems are covered by the backup process?")
        elif "access" in gap_text or "account" in gap_text:
            questions.append("Which accounts can read, modify, delete, or administer backups?")
        elif "storage" in gap_text or "resilient" in gap_text:
            questions.append("How are backups stored securely and resiliently?")
        else:
            questions.append(f"What evidence can you provide to address: {getattr(gap, 'gap', str(gap))}?")
    return list(dict.fromkeys(questions))


def _load_agent_json(text: str) -> dict:
    """Load JSON from model output, including common markdown-wrapped responses."""
    if not isinstance(text, str):
        raise ValueError("Agent output is not text")

    stripped = text.strip()
    candidates = [stripped]

    fenced = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        candidates.insert(0, fenced.group(1).strip())

    first = stripped.find("{")
    last = stripped.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidates.append(stripped[first:last + 1])

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    raise ValueError("No JSON object found in agent output")


def _call_openai_agent(api_key: str, model: str, role: str, prompt: str, base_url: str | None = None, max_tokens: int = 1024) -> str:
    """Call an OpenAI-compatible API for a single agent role."""
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": f"""You are the {role} for E8 Compass Portal.

REFERENCE: Australian Signals Directorate Essential Eight Maturity Model (November 2023):
{E8_KNOWLEDGE}

Assess the user-provided evidence against the ASD E8 maturity levels above. Policy statements are weak evidence. Be concise and accurate. Return valid JSON only."""},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    # json_object not supported by older models like gpt-4
    if "gpt-4" != model.lower() and "gpt-4-" not in model.lower():
        kwargs["response_format"] = {"type": "json_object"}
    completion = client.chat.completions.create(**kwargs)
    text = completion.choices[0].message.content or "{}"
    return text


async def _stream_openai_agent(api_key, model, role, prompt, base_url=None):
    """Stream OpenAI-compatible API, yielding text chunks."""
    import asyncio
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    # Use non-streaming call in thread, then chunk the result
    full_text = await asyncio.to_thread(_call_openai_agent, api_key, model, role, prompt, base_url)
    # Simulate streaming by yielding chunks
    chunk_size = 3
    for i in range(0, len(full_text), chunk_size):
        yield full_text[i:i+chunk_size]
        await asyncio.sleep(0.02)
