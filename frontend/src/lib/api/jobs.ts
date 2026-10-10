import { apiRequest } from "@/lib/api/client";

export type RequirementGroup = "technology" | "experience" | "education" | "responsibility" | "preferred";

export interface JDAnalysisCreate {
  title: string;
  company?: string | null;
  source_url?: string | null;
  source_text: string;
}

export interface JDRequirement {
  id: string;
  position: number;
  group: RequirementGroup;
  quote: string;
  source_start: number;
  source_end: number;
  evidence_type: "FACT_FROM_JD";
  normalized_name: string | null;
  interpretation_type: "NORMALIZED_INTERPRETATION" | null;
}

export interface JDAnalysisSummary {
  id: string;
  title: string;
  company: string | null;
  source_url: string | null;
  created_at: string;
  extractor_version: string;
  requirement_count: number;
  truncated: boolean;
}

export interface JDAnalysis extends JDAnalysisSummary {
  source_text: string;
  requirements: JDRequirement[];
}

export interface JDAnalysisList {
  items: JDAnalysisSummary[];
  total: number;
  limit: number;
  offset: number;
}

export function createJDAnalysis(accessToken: string, body: JDAnalysisCreate, signal?: AbortSignal) {
  return apiRequest<JDAnalysis>("/jobs/analyses", { method: "POST", accessToken, body, signal });
}

export function listJDAnalyses(accessToken: string, limit = 10, offset = 0, signal?: AbortSignal) {
  return apiRequest<JDAnalysisList>(`/jobs/analyses?limit=${limit}&offset=${offset}`, {
    method: "GET", accessToken, signal, cache: "no-store",
  });
}

export function getJDAnalysis(accessToken: string, id: string, signal?: AbortSignal) {
  return apiRequest<JDAnalysis>(`/jobs/analyses/${encodeURIComponent(id)}`, {
    method: "GET", accessToken, signal, cache: "no-store",
  });
}

export interface JDMatch {
  analysis_id: string;
  status: "AVAILABLE" | "UNAVAILABLE";
  unavailable_reason: string | null;
  snapshot_version: number | null;
  snapshot_created_at: string | null;
  evaluated_at: string;
  model_version: string;
  matching_version: string;
  extractor_version: string;
  interpretation: string;
  alignment: { label: string; value: number | null; numerator: number; denominator: number; eligible_technologies: string[]; methodology: string };
  requirements: {
    requirement: JDRequirement;
    canonical_technology: string | null;
    strength: string;
    strength_explanation: string;
    state: "EVIDENCE_BACKED_ALIGNMENT" | "EVIDENCE_NEEDS_STRENGTHENING" | "MISSING_EVIDENCE" | "NOT_ASSESSED" | "UNKNOWN_OR_UNMAPPED";
    evidence: { evidence_count: number; source_types: string[]; evidence_families: string[]; evidence_confidence: number | null; assessment_measurement: number | null; measurement_status: string };
    explanation: string;
    included_in_alignment: boolean;
    exclusion_reason: string | null;
    actions: { label: string; href: "/evidence" | "/assessment" | "/roadmap" | "/certifications"; provenance: string }[];
  }[];
}

export function getJDMatch(accessToken: string, id: string, signal?: AbortSignal) {
  return apiRequest<JDMatch>(`/jobs/analyses/${encodeURIComponent(id)}/match`, { accessToken, signal, cache: "no-store" });
}
