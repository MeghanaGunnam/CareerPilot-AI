import { apiRequest } from "@/lib/api/client";

export interface AssessmentSummary {
  id: string;
  skill_id: string;
  skill_name: string;
  title: string;
  description: string;
  difficulty: string;
  version: number;
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

export interface AssessmentDetail extends AssessmentSummary {
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
  explanation: string;
}

export interface AssessmentSubmissionResponse {
  attempt_id: string;
  assessment_id: string;
  skill_id: string;
  skill_name: string;
  status: string;
  raw_score: number;
  total_questions: number;
  percentage: number;
  completed_at: string;
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
  rationale: string | null;
}

export interface AssessmentRecommendation {
  assessment_id: string;
  skill_id: string;
  skill_name: string;
  title: string;
  description: string;
  difficulty: string;
  version: number;
  competency: AssessmentRecommendationCompetency;
  recommendation_status: string;
  reason: string;
}

export interface CareerAssessmentRecommendationsResponse {
  career_id: string;
  career_title: string;
  onet_soc_code: string;
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