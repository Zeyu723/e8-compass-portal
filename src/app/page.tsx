"use client";

import { useRef, useState } from "react";
import { Shield, FileText, Upload, Brain, SearchCheck, AlertTriangle, CheckCircle, Server, BarChart3, Download, ChevronRight, Loader2, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import type { AssessmentResponse, AssessmentScope, EssentialEightControl, InputType } from "@/lib/types";
import { fetchDemoResult, submitAssessment, streamAssessment, SAMPLE_POLICY, CONTROLS, SCOPES, INPUT_TYPES } from "@/lib/api";
import type { SSEEvent } from "@/lib/api";

const MAX_CONTENT_LENGTH = 20000;
const TEXT_FILE_EXTENSIONS = [".txt", ".md", ".csv", ".json", ".log"];

const SCOPE_HELP: Record<AssessmentScope, string> = {
  "Whole document": "Broad review of a full document; agents look for coverage and limitations.",
  "Part of a document": "Focused review of an excerpt; agents avoid over-claiming beyond the text.",
  "Tool output": "Implementation evidence such as exports, logs, scan output, or command results.",
  "Evidence file": "Supporting evidence; agents check provenance, date, scope, and proof strength.",
};

const INPUT_HELP: Record<InputType, string> = {
  Policy: "Policy-only evidence is weak: it shows intent, not implementation.",
  Text: "Manual text is assessed by detail, scope, and whether it proves implementation.",
  "Tool output": "Tool output can be stronger when it includes logs, configuration, or results.",
  Evidence: "Evidence is stronger when dated, scoped, and tied to specific systems or controls.",
};

function contentLabel(inputType: InputType) {
  if (inputType === "Tool output") return "Tool Output Content";
  if (inputType === "Evidence") return "Evidence Content";
  if (inputType === "Text") return "Assessment Text";
  return "Policy / Evidence Content";
}

function fileExtension(name: string) {
  const lower = name.toLowerCase();
  const dot = lower.lastIndexOf(".");
  return dot >= 0 ? lower.slice(dot) : "";
}

const AGENT_META: Record<string, { icon: React.ReactNode; color: string }> = {
  "Document Reader Agent": { icon: <FileText className="h-4 w-4" />, color: "bg-blue-500" },
  "Essential Eight Mapper Agent": { icon: <SearchCheck className="h-4 w-4" />, color: "bg-indigo-500" },
  "Evidence Checker Agent": { icon: <AlertTriangle className="h-4 w-4" />, color: "bg-amber-500" },
  "Critic Agent": { icon: <AlertTriangle className="h-4 w-4" />, color: "bg-red-500" },
  "Guidance Writer Agent": { icon: <Brain className="h-4 w-4" />, color: "bg-emerald-500" },
};

function severityColor(s: string) {
  if (s === "High") return "destructive" as const;
  if (s === "Medium") return "secondary" as const;
  return "outline" as const;
}

function priorityColor(p: string) {
  if (p === "High") return "destructive" as const;
  if (p === "Medium") return "secondary" as const;
  return "outline" as const;
}

function bandColor(b: string) {
  if (b === "Low") return "bg-red-100 text-red-800 border-red-300";
  if (b === "Medium") return "bg-amber-100 text-amber-800 border-amber-300";
  if (b === "Good") return "bg-emerald-100 text-emerald-800 border-emerald-300";
  return "bg-green-100 text-green-800 border-green-300";
}

function statusColor(s: string) {
  if (s.includes("Insufficient") || s === "Not Compliant") return "bg-red-100 text-red-800 border-red-300";
  if (s === "Partial") return "bg-amber-100 text-amber-800 border-amber-300";
  if (s === "Compliant") return "bg-green-100 text-green-800 border-green-300";
  return "bg-gray-100 text-gray-800 border-gray-300";
}

export default function Home() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [scope, setScope] = useState<AssessmentScope>("Part of a document");
  const [control, setControl] = useState<EssentialEightControl>("Regular Backups");
  const [inputType, setInputType] = useState<InputType>("Policy");
  const [content, setContent] = useState(SAMPLE_POLICY);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [result, setResult] = useState<AssessmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeAgents, setActiveAgents] = useState<number>(0);
  const [streamFindings, setStreamFindings] = useState<Record<string, string>>({});
  const [currentModel, setCurrentModel] = useState<string>("");

  async function handleFileSelected(file: File | null) {
    if (!file) return;
    setError(null);
    setUploadStatus(`Reading ${file.name}...`);

    const extension = fileExtension(file.name);
    try {
      let extracted = "";
      if (TEXT_FILE_EXTENSIONS.includes(extension)) {
        extracted = await file.text();
      } else if (extension === ".docx") {
        const mammoth = await import("mammoth/mammoth.browser");
        const buffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer: buffer });
        extracted = result.value;
      } else if (extension === ".pdf") {
        throw new Error("PDF parsing is not enabled in this demo. Please paste extracted text or upload .txt/.md/.docx.");
      } else {
        throw new Error("Unsupported file type. Use .txt, .md, .csv, .json, .log, or .docx.");
      }

      const trimmed = extracted.trim();
      if (!trimmed) {
        throw new Error("No readable text was found in this file.");
      }

      const truncated = trimmed.length > MAX_CONTENT_LENGTH;
      setContent(truncated ? trimmed.slice(0, MAX_CONTENT_LENGTH) : trimmed);
      if (inputType !== "Tool output") setInputType("Evidence");
      setScope(extension === ".docx" ? "Evidence file" : scope);
      setUploadStatus(
        `${file.name} loaded: ${Math.min(trimmed.length, MAX_CONTENT_LENGTH).toLocaleString()} characters${truncated ? " (truncated to API limit)" : ""}.`,
      );
    } catch (err) {
      setUploadStatus(null);
      setError((err as Error).message);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleRun() {
    if (control !== "Regular Backups") {
      setError("MVP assessment is implemented for Regular Backups only. Other controls are available as reference in the portal knowledge base.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setActiveAgents(0);
    setStreamFindings({});
    setCurrentModel("");

    streamAssessment(
      { scope, control, input_type: inputType, content },
      (event: SSEEvent) => {
        if (event.type === "agent_start") {
          setActiveAgents((prev) => prev + 1);
          setCurrentModel(event.model);
          setStreamFindings((prev) => ({ ...prev, [event.agent]: `Analyzing with ${event.model}...` }));
        } else if (event.type === "agent_chunk") {
          setStreamFindings((prev) => ({
            ...prev,
            [event.agent]: (prev[event.agent] || "") + event.chunk,
          }));
        } else if (event.type === "agent_done") {
          setStreamFindings((prev) => ({ ...prev, [event.agent]: event.finding }));
        } else if (event.type === "done") {
          setResult(event.result);
          setLoading(false);
        }
      },
      () => {
        // Fallback to non-streaming
        submitAssessment({ scope, control, input_type: inputType, content })
          .then(setResult)
          .catch(() => fetchDemoResult().then(setResult))
          .finally(() => setLoading(false));
      },
      () => {
        setLoading(false);
      },
    );
  }

  async function handleDemo() {
    setLoading(true);
    setError(null);
    setActiveAgents(0);

    const agentInterval = setInterval(() => {
      setActiveAgents((prev) => Math.min(prev + 1, 5));
    }, 500);

    setTimeout(() => {
      clearInterval(agentInterval);
      setActiveAgents(5);
      fetchDemoResult()
        .then(setResult)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 2800);
  }

  const allAgents = result ? result.agent_review.map((a) => ({
    agent: a.agent,
    finding: streamFindings[a.agent] || a.finding,
  })) : [
    { agent: "Document Reader Agent", finding: streamFindings["Document Reader Agent"] || "" },
    { agent: "Essential Eight Mapper Agent", finding: streamFindings["Essential Eight Mapper Agent"] || "" },
    { agent: "Evidence Checker Agent", finding: streamFindings["Evidence Checker Agent"] || "" },
    { agent: "Critic Agent", finding: streamFindings["Critic Agent"] || "" },
    { agent: "Guidance Writer Agent", finding: streamFindings["Guidance Writer Agent"] || "" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto max-w-[1600px] px-3 sm:px-6 py-3 sm:py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">E8 Compass Portal</h1>
              <p className="text-xs text-muted-foreground">AI-guided Essential Eight Self-Assessment</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              <Server className="mr-1 h-3 w-3" />
              API: {process.env.NEXT_PUBLIC_API_BASE_URL || "23.254.236.178:8000"}
            </Badge>
            {result && (
              <Badge variant={result.metadata.used_fallback ? "secondary" : "default"} className="text-xs">
                {result.metadata.ai_mode === "live" ? "Live AI" : "Demo Mode"}
              </Badge>
            )}
            {loading && !result && currentModel && (
              <Badge variant="default" className="text-xs animate-pulse">
                Streaming: {currentModel}
              </Badge>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] px-3 sm:px-6 py-3 sm:py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
          {/* LEFT: Assessment Wizard */}
          <div className="lg:col-span-3 space-y-3 sm:space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Upload className="h-4 w-4 text-blue-600" />
                  Assessment Wizard
                </CardTitle>
                <CardDescription className="text-xs">Configure and run your assessment</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Scope */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Scope</label>
                  <div className="grid grid-cols-1 gap-1">
                    {SCOPES.map((s) => (
                      <button
                        key={s}
                        onClick={() => setScope(s)}
                        className={`text-left text-xs px-3 py-1.5 rounded-md border transition-colors ${
                          scope === s ? "bg-blue-50 border-blue-300 text-blue-800" : "hover:bg-gray-50"
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] leading-relaxed text-muted-foreground">{SCOPE_HELP[scope]}</p>
                </div>

                <Separator />

                {/* Control */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Essential Eight Control</label>
                  <div className="grid grid-cols-1 gap-1">
                    {CONTROLS.map((c) => (
                      <button
                        key={c}
                        onClick={() => setControl(c)}
                        className={`text-left text-xs px-3 py-1.5 rounded-md border transition-colors ${
                          control === c ? "bg-blue-50 border-blue-300 text-blue-800" : "hover:bg-gray-50"
                        }`}
                      >
                        {c}
                      </button>
                    ))}
                  </div>
                  {control !== "Regular Backups" && (
                    <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-[11px] leading-relaxed text-amber-800">
                      This MVP runs live assessment for Regular Backups only. Other controls are shown for roadmap and reference.
                    </div>
                  )}
                </div>

                <Separator />

                {/* Input Type */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Input Type</label>
                  <div className="grid grid-cols-2 gap-1">
                    {INPUT_TYPES.map((t) => (
                      <button
                        key={t}
                        onClick={() => setInputType(t)}
                        className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                          inputType === t ? "bg-blue-50 border-blue-300 text-blue-800" : "hover:bg-gray-50"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] leading-relaxed text-muted-foreground">{INPUT_HELP[inputType]}</p>
                </div>

                <Separator />

                {/* Content */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <label className="text-xs font-medium text-muted-foreground">{contentLabel(inputType)}</label>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 text-[11px]"
                      disabled={loading}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload className="mr-1 h-3 w-3" />
                      Upload Evidence
                    </Button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      accept=".txt,.md,.csv,.json,.log,.docx,.pdf"
                      onChange={(event) => handleFileSelected(event.target.files?.[0] ?? null)}
                    />
                  </div>
                  <Textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={8}
                    className="text-xs font-mono"
                    placeholder="Paste your policy text here..."
                  />
                  {uploadStatus && (
                    <p className="text-[11px] leading-relaxed text-emerald-700">{uploadStatus}</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleRun} disabled={loading || !content.trim()} className="flex-1 text-xs" size="sm">
                    {loading ? (
                      <><Loader2 className="mr-1 h-3 w-3 animate-spin" /> Running...</>
                    ) : (
                      <><Zap className="mr-1 h-3 w-3" /> Run Assessment</>
                    )}
                  </Button>
                  <Button onClick={handleDemo} disabled={loading} variant="outline" size="sm" className="text-xs">
                    Demo
                  </Button>
                </div>

                {error && (
                  <div className="rounded-md bg-red-50 border border-red-200 p-2 text-xs text-red-700">
                    {error}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Supported Inputs */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">Supported Inputs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1">
                  {["Policy document", "RSOP output", "Entra ID report", "ASD PowerShell", "Patch register", "Backup test record", "Asset inventory", "Screenshots"].map((item) => (
                    <Badge key={item} variant="outline" className="text-[10px]">{item}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* MIDDLE: Agent Review */}
          <div className="lg:col-span-4 space-y-3 sm:space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Brain className="h-4 w-4 text-purple-600" />
                  AI Review Council
                </CardTitle>
                <CardDescription className="text-xs">Multi-agent evidence review pipeline</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {allAgents.map((a, i) => {
                  const meta = AGENT_META[a.agent] || { icon: <Brain className="h-4 w-4" />, color: "bg-gray-500" };
                  const finding = String(a.finding || streamFindings[a.agent] || "");
                  const isWaiting = loading && !result && i >= activeAgents;
                  const isThinking = loading && !result && i < activeAgents && (finding.includes("Analyzing") || !finding);
                  const isDone = !!(result || (loading && i < activeAgents && finding && !finding.includes("Analyzing")));

                  const bgClass = isThinking ? "border-blue-300 bg-blue-50 shadow-sm" :
                    isDone && result ? "border-green-200 bg-green-50" :
                    "border-gray-200 bg-white";

                  return (
                    <div key={i} className={`rounded-lg border p-3 transition-all duration-300 ${bgClass}`}>
                      <div className="flex items-center gap-2 mb-1">
                        <div className={`flex h-6 w-6 items-center justify-center rounded-full text-white ${meta.color}`}>
                          {meta.icon}
                        </div>
                        <span className="text-xs font-semibold">{a.agent}</span>
                        {isThinking && <Loader2 className="h-3 w-3 animate-spin text-blue-500 ml-auto" />}
                        {isDone && <CheckCircle className="h-3 w-3 text-green-500 ml-auto" />}
                      </div>
                      {isWaiting && <Skeleton className="h-3 w-full mt-2" />}
                      {isThinking && (
                        <p className="text-xs text-muted-foreground mt-1">
                          <Loader2 className="h-3 w-3 animate-spin inline mr-1" />
                          {finding || "Analyzing..."}
                        </p>
                      )}
                      {isDone && (
                        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                          {finding || "Waiting..."}
                        </p>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* RIGHT: Dashboard Report */}
          <div className="lg:col-span-5 space-y-3 sm:space-y-4">
            {!result && !loading && (
              <Card className="flex items-center justify-center h-48 sm:h-96">
                <div className="text-center text-muted-foreground">
                  <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm font-medium">Guidance Dashboard</p>
                  <p className="text-xs">Run an assessment to see results</p>
                </div>
              </Card>
            )}

            {loading && !result && (
              <Card>
                <CardContent className="py-8 text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-3 text-blue-500" />
                  <p className="text-sm font-medium">Analyzing evidence...</p>
                  <p className="text-xs text-muted-foreground mt-1">AI agents are reviewing your input</p>
                  <Progress value={(activeAgents / 5) * 100} className="mt-4" />
                </CardContent>
              </Card>
            )}

            {result && (
              <>
                {/* Status Header */}
                <Card>
                  <CardContent className="py-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div>
                        <p className="text-xs text-muted-foreground">Control Assessment</p>
                        <p className="text-lg font-bold">{result.assessment.control}</p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 sm:gap-3 sm:text-right">
                        <div>
                          <span className={`inline-block rounded-full border px-4 py-1.5 text-sm font-bold ${statusColor(result.final_result.status)}`}>
                            {result.final_result.status}
                          </span>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">Evidence Quality</p>
                          <span className={`inline-block rounded-full border px-3 py-1 text-xs font-semibold ${bandColor(result.evidence_quality.confidence_band)}`}>
                            {result.evidence_quality.confidence_band} ({result.evidence_quality.confidence_score})
                          </span>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-muted-foreground">AI Mode</p>
                          <Badge variant={result.metadata.used_fallback ? "secondary" : "default"} className="text-xs">
                            {result.metadata.used_fallback ? "Demo" : "Live"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Evidence Found + Gaps */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Evidence Found
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-1">
                        {result.evidence_found.map((e, i) => (
                          <li key={i} className="text-xs flex items-start gap-2">
                            <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 shrink-0" />
                            <span>{e}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                        Key Gaps
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-1.5">
                        {result.gaps.map((g, i) => (
                          <li key={i} className="text-xs flex items-start gap-2">
                            <Badge variant={severityColor(g.severity)} className="text-[10px] px-1.5 py-0 shrink-0">
                              {g.severity}
                            </Badge>
                            <span>{g.gap}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </div>

                {/* Clarification Questions */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <SearchCheck className="h-4 w-4 text-blue-500" />
                      Clarification Questions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ol className="space-y-1.5">
                      {result.clarification_questions.map((q, i) => (
                        <li key={i} className="text-xs flex items-start gap-2">
                          <span className="text-blue-500 font-bold shrink-0">{i + 1}.</span>
                          <span>{q}</span>
                        </li>
                      ))}
                    </ol>
                  </CardContent>
                </Card>

                {/* Recommendations */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <ChevronRight className="h-4 w-4 text-emerald-500" />
                      Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {result.recommendations.map((r, i) => (
                        <div key={i} className="rounded-md border p-2.5">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant={priorityColor(r.priority)} className="text-[10px] px-1.5 py-0">
                              {r.priority}
                            </Badge>
                            <span className="text-xs font-medium">{r.action}</span>
                          </div>
                          <p className="text-[11px] text-muted-foreground">{r.reason}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Summary */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs leading-relaxed text-muted-foreground">{result.final_result.summary}</p>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>

        {/* Bottom: JSON Debug */}
        {result && (
          <div className="mt-4 sm:mt-6">
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xs text-muted-foreground flex items-center gap-2">
                    <Download className="h-3 w-3" />
                    API Response JSON
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs h-6"
                    onClick={async () => {
                      try { await navigator.clipboard.writeText(JSON.stringify(result, null, 2)); } catch {}
                    }}
                  >
                    Copy
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <pre className="text-[10px] font-mono bg-gray-900 text-green-400 rounded-md p-4 overflow-auto max-h-64 leading-relaxed">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
