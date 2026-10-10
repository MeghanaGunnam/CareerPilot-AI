import { apiRequest } from "@/lib/api/client";

export interface CertificationRecommendation {
  key: string;
  name: string;
  provider: string;
  category: string;
  relevant_skills: string[];
  priority: number;
  reason: string;
  gaps: {
    skill: string;
    state: "MISSING_EVIDENCE" | "EVIDENCE_NEEDS_STRENGTHENING";
  }[];
  official_url: string;
  provenance: {
    source: string;
    catalog_version: string;
    source_url: string;
    url_checked_on: string;
    verification_status: "OFFICIAL_PAGE_RETRIEVED" | "FETCH_BLOCKED_HTTP_403";
    verification_note: string;
    coverage_basis: string;
    limitations: string;
  };
}

export interface CertificationRecommendationsResponse {
  target_role: string;
  occupational_anchor: { id: string; title: string; onet_soc_code: string };
  snapshot_version: number;
  model_version: string;
  methodology: string;
  recommendations: CertificationRecommendation[];
  interpretation: string;
}

export function getCertificationRecommendations(accessToken: string, signal?: AbortSignal) {
  return apiRequest<CertificationRecommendationsResponse>("/certification-recommendations", {
    accessToken,
    signal,
    cache: "no-store",
  });
}
