import { apiRequest } from "@/lib/api/client";

export interface RecordedCounts { skill_records: number | null; evidence_entries: number | null; assessment_evidence_entries: number | null }
export interface ProgressSnapshot { id: string; version: number; schema_version: string; created_at: string; trigger_type: string; counts: RecordedCounts }
export interface CareerProgress {
  career_twin_id: string | null;
  history_status: "COMPARABLE_HISTORY" | "NOT_ENOUGH_HISTORY";
  history_message: string;
  current_snapshot: ProgressSnapshot | null;
  previous_snapshot: ProgressSnapshot | null;
  comparison: { key: string; label: string; current_recorded_value: number | null; previous_recorded_value: number | null; change: number | null }[];
  snapshots: ProgressSnapshot[];
  snapshot_total: number;
  limit: number;
  offset: number;
  events: { id: string; event_type: string; source_type: string; occurred_at: string; snapshot_version: number | null }[];
  event_total: number;
  event_offset: number;
  roadmap_status_counts: Record<string, number>;
  roadmap_total: number;
  completed_assessment_attempts: number;
  interpretation: string;
}

export const getProgress = (accessToken: string, offset: number, eventOffset: number, signal?: AbortSignal) => apiRequest<CareerProgress>(`/career-twin/progress?limit=20&offset=${offset}&event_offset=${eventOffset}`, { accessToken, signal, cache: "no-store" });
