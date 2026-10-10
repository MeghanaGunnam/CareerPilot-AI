import { apiRequest } from "@/lib/api/client";

export interface AssessmentSummary {
  id: string;
  skill_id: string;
  skill_name: string;
  title: string;
  description: string | null;
  difficulty: string;
  version: number;
  question_count: number;
  latest_attempt: AssessmentAttemptSummary | null;
}

export interface AssessmentOption {
  key: string;
  text: string;
}

export interface AssessmentQuestion {
  id: string;
  position: number;
  question_text: string;
  options: AssessmentOption[];
}

export interface AssessmentDetail extends Omit<AssessmentSummary, "question_count" | "latest_attempt"> {
  questions: AssessmentQuestion[];
}

export interface AssessmentAnswer {
  question_id: string;
  selected_option: string;
}

export interface AssessmentSubmissionRequest {
  answers: AssessmentAnswer[];
}

export interface AssessmentResultAnswer {
  question_id: string;
  selected_option: string;
  correct_option: string;
  is_correct: boolean;
  explanation: string | null;
}

export interface AssessmentAttemptSummary {
  attempt_id: string;
  assessment_id: string;
  assessment_title: string;
  assessment_version: number;
  skill_id: string;
  skill_name: string;
  status: string;
  raw_score: number | null;
  total_questions: number | null;
  percentage: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface AssessmentSubmissionResponse extends AssessmentAttemptSummary {
  answers: AssessmentResultAnswer[];
}

export interface AssessmentRecommendationCompetency {
  element_id: string;
  element_name: string;
  skill_type: string;
  importance: number | null;
  level: number | null;
  mapping_type: string;
  mapping_version: string;
  mapping_rationale: string | null;
}

export interface AssessmentRecommendation {
  assessment_id: string;
  skill_id: string;
  skill_name: string;
  title: string;
  description: string | null;
  difficulty: string;
  version: number;
  competency: AssessmentRecommendationCompetency | null;
  recommendation_status: string;
  reason: string;
}

export interface CareerAssessmentRecommendationsResponse {
  career_id: string;
  career_title: string;
  onet_soc_code: string | null;
  recommended_count: number;
  recommendations: AssessmentRecommendation[];
  interpretation: string;
}

export async function getAssessments(
  accessToken: string
): Promise<AssessmentSummary[]> {
  return apiRequest<AssessmentSummary[]>("/assessments", {
    method: "GET",
    accessToken,
  });
}

export async function getAssessment(
  accessToken: string,
  assessmentId: string
): Promise<AssessmentDetail> {
  return apiRequest<AssessmentDetail>(
    `/assessments/${assessmentId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function submitAssessment(
  accessToken: string,
  assessmentId: string,
  payload: AssessmentSubmissionRequest
): Promise<AssessmentSubmissionResponse> {
  return apiRequest<AssessmentSubmissionResponse>(
    `/assessments/${assessmentId}/submit`,
    {
      method: "POST",
      accessToken,
      body: payload,
    }
  );
}

export async function getCareerAssessmentRecommendations(
  accessToken: string,
  careerId: string
): Promise<CareerAssessmentRecommendationsResponse> {
  return apiRequest<CareerAssessmentRecommendationsResponse>(
    `/assessments/recommendations/careers/${careerId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getAssessmentAttempts(accessToken: string, offset = 0): Promise<AssessmentAttemptSummary[]> {
  return apiRequest<AssessmentAttemptSummary[]>(`/assessments/attempts?limit=50&offset=${offset}`, {
    method: "GET",
    accessToken,
  });
}

export function getMyAssessmentRecommendations(accessToken: string) {
  return apiRequest<CareerAssessmentRecommendationsResponse>("/assessments/recommendations/me", { accessToken });
}

export async function getAssessmentAttempt(accessToken: string, attemptId: string): Promise<AssessmentSubmissionResponse> {
  return apiRequest<AssessmentSubmissionResponse>(`/assessments/attempts/${encodeURIComponent(attemptId)}`, {
    method: "GET",
    accessToken,
  });
}
