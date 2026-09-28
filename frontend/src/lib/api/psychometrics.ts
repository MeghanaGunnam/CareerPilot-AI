import { apiRequest } from "./client";

export interface RiasecQuestion {
  id: string;
  dimension: string;
  text: string;
}

export interface RiasecResponseOption {
  value: number;
  label: string;
}

export interface RiasecQuestionnaire {
  assessment_version: string;
  instructions: string;
  questions: RiasecQuestion[];
  response_options: RiasecResponseOption[];
}

export interface RiasecAnswer {
  question_id: string;
  response_value: number;
}

export interface RiasecScores {
  realistic: number;
  investigative: number;
  artistic: number;
  social: number;
  enterprising: number;
  conventional: number;
}

export interface RiasecProfile {
  id: string;
  assessment_id: string;
  scores: RiasecScores;
  dominant_code: string;
  scoring_version: string;
  created_at: string;
}

export interface RiasecAssessmentResult {
  assessment_id: string;
  assessment_version: string;
  status: string;
  completed_at: string;
  profile: RiasecProfile;
}

export interface CareerInterestMatch {
  career_id: string;
  onet_soc_code: string;
  title: string;
  description: string | null;
  job_zone: number | null;
  interest_alignment: number;
  interest_alignment_percent: number;
  career_riasec: RiasecScores;
  dominant_code: string;
}

export async function getRiasecQuestions(
  accessToken: string
): Promise<RiasecQuestionnaire> {
  return apiRequest<RiasecQuestionnaire>(
    "/psychometrics/riasec/questions",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function submitRiasecAssessment(
  accessToken: string,
  answers: RiasecAnswer[]
): Promise<RiasecAssessmentResult> {
  return apiRequest<RiasecAssessmentResult>(
    "/psychometrics/riasec/assessments",
    {
      method: "POST",
      accessToken,
      body: {
        answers,
      },
    }
  );
}

export async function getLatestRiasecAssessment(
  accessToken: string
): Promise<RiasecAssessmentResult> {
  return apiRequest<RiasecAssessmentResult>(
    "/psychometrics/riasec/latest",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getRiasecMatches(
  accessToken: string,
  limit = 10
): Promise<CareerInterestMatch[]> {
  return apiRequest<CareerInterestMatch[]>(
    `/psychometrics/riasec/matches?limit=${limit}`,
    {
      method: "GET",
      accessToken,
    }
  );
}