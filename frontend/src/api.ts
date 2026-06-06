import type { Case, CaseSummary, JudgeResponse, Verdict } from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL || "https://med-warrant-production.up.railway.app";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listCases: () => request<CaseSummary[]>("/api/cases"),

  getCase: (id: string) => request<Case>(`/api/cases/${id}`),

  judge: (case_id: string) =>
    request<JudgeResponse>("/api/judge", {
      method: "POST",
      body: JSON.stringify({ case_id }),
    }),

  searchEvidence: (_q: string): Promise<never> => {
    throw new Error("searchEvidence: not implemented until Phase 6");
  },

  getQueue: () => request<Verdict[]>("/api/queue"),

  review: (body: { verdict_id: string; decision: string; note: string }) =>
    request<Verdict>("/api/review", {
      method: "POST",
      body: JSON.stringify(body),
    }),
} as const;
