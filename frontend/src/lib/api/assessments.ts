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