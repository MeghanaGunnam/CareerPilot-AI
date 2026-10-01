import { apiRequest } from "@/lib/api/client";

export interface SkillEvidence {
  id: string;
  source_type: string;
  source_reference: string;
  source_section: string | null;
  evidence_text: string | null;
  evidence_status: string;
  evidence_strength: number | null;
  observed_at: string;
}

export interface StudentSkill {
  id: string;
  skill_id: string;
  canonical_name: string;
  category: string | null;

  claimed_proficiency: number | null;
  estimated_proficiency: number | null;
  evidence_confidence: number | null;
  freshness_score: number | null;
  last_verified_at: string | null;

  evidence: SkillEvidence[];
}

export interface MySkillsResponse {
  total_skills: number;
  total_evidence: number;
  skills: StudentSkill[];
}

export async function getMySkills(
  accessToken: string
): Promise<MySkillsResponse> {
  return apiRequest<MySkillsResponse>("/skills/me", {
    method: "GET",
    accessToken,
  });
}