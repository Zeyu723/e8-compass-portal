import type { AssessmentRequest, AssessmentResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

export async function fetchDemoResult(): Promise<AssessmentResponse> {
  const res = await fetch(`${API_BASE}/demo/sample-result`);
  if (!res.ok) throw new Error(`Demo fetch failed: ${res.status}`);
  return res.json();
}

export function submitAssessment(request: AssessmentRequest): Promise<AssessmentResponse> {
  return fetch(`${API_BASE}/assessments/regular-backups`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  }).then(r => r.ok ? r.json() : Promise.reject(new Error(`Assessment failed: ${r.status}`)));
}

export type SSEEvent = 
  | { type: "agent_start"; agent: string; model: string }
  | { type: "agent_done"; agent: string; finding: string }
  | { type: "agent_chunk"; agent: string; chunk: string }
  | { type: "done"; result: AssessmentResponse }
  | { type: "error"; message: string };

export function streamAssessment(
  request: AssessmentRequest,
  onEvent: (event: SSEEvent) => void,
  onError: (err: Error) => void,
  onDone: () => void,
): AbortController {
  const controller = new AbortController();
  (async () => {
    try {
      const res = await fetch(`${API_BASE}/assessments/regular-backups/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`Stream failed: ${res.status}`);
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));
              onEvent(event);
              if (event.type === "done" || event.type === "error") { onDone(); return; }
            } catch { /* skip */ }
          }
        }
      }
      onDone();
    } catch (err) {
      if ((err as Error).name !== "AbortError") onError(err as Error);
      onDone();
    }
  })();
  return controller;
}

export const SAMPLE_POLICY = `The organisation performs weekly backups of important business systems.
Backups are stored on internal infrastructure.
Restore testing may be performed when required.
The IT team is responsible for backup operations.`;

export const CONTROLS = [
  "Patch Applications",
  "Patch Operating Systems",
  "Multi-factor Authentication",
  "Restrict Administrative Privileges",
  "Application Control",
  "Restrict Microsoft Office Macros",
  "User Application Hardening",
  "Regular Backups",
] as const;

export const SCOPES = ["Whole document", "Part of a document", "Tool output", "Evidence file"] as const;
export const INPUT_TYPES = ["Policy", "Text", "Tool output", "Evidence"] as const;

export const AGENT_ICONS: Record<string, string> = {
  "Document Reader Agent": "FileText",
  "Essential Eight Mapper Agent": "Map",
  "Evidence Checker Agent": "SearchCheck",
  "Critic Agent": "AlertTriangle",
  "Guidance Writer Agent": "Brain",
};
