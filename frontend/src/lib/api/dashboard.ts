import { apiRequest } from "@/lib/api/client";
import type { AssistantStatus } from "./assistant";
import type { JDAnalysisSummary, JDMatch } from "./jobs";

export interface DashboardSummary {
  resume_count: number;
  completed_assessment_attempts: number;
  roadmap_status_counts: Record<string, number>;
  roadmap_total: number;
  certification_status: "AVAILABLE" | "UNAVAILABLE";
  certification_preview: { name: string; provider: string }[];
  latest_jd: JDAnalysisSummary | null;
  latest_alignment: JDMatch["alignment"] | null;
  application_status_counts: Record<string, number>;
  application_total: number;
  progress: { message: string; snapshot_version: number | null; evidence_entry_change: number | null };
  assistant: AssistantStatus;
}
export const getDashboardSummary = (accessToken: string, signal?: AbortSignal) => apiRequest<DashboardSummary>("/dashboard/summary", { accessToken, signal, cache: "no-store" });
