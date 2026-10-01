import { apiRequest } from "@/lib/api/client";

export interface CareerInfo {
  id: string;
  onet_soc_code: string;
  title: string;
  job_zone: number | null;
  onet_version: string;
}

export interface ReadinessMetric {
  score: number | null;
  status: string;
  interpretation?: string;

  strong_evidence_count?: number;
  weak_evidence_count?: number;
  missing_evidence_count?: number;
  total_market_signals?: number;

  evidenced_technology_count?: number;

  measured_competency_count?: number;
  total_competency_count?: number;
}

export interface ReadinessDimensions {
  interest_alignment: ReadinessMetric;
  technology_evidence_coverage: ReadinessMetric;
  technology_evidence_strength: ReadinessMetric;
  competency_measurement_coverage: ReadinessMetric;

  overall_readiness_score: number | null;
  overall_readiness_status: string;
  interpretation: string;
}

export interface CareerReadinessResponse {
  career_twin_id: string;
  snapshot_version: number;
  model_version: string;
  career: CareerInfo;
  readiness: ReadinessDimensions;
}

export interface TechnologyEvidenceItem {
  technology: string;
  normalized_technology: string;
  element_name: string;
  hot_technology: boolean;
  in_demand: boolean;

  student_skill?: string;
  evidence_confidence?: number | null;
  estimated_proficiency?: number | null;
  verified_skill_state?: number | null;
  evidence_families?: string[];

  gap_status: string;
  interpretation?: string;
}

export interface TechnologyGapAnalysis {
  strong_evidence: TechnologyEvidenceItem[];

  evidence_needs_strengthening:
    TechnologyEvidenceItem[];

  missing_evidence: TechnologyEvidenceItem[];

  summary: {
    strong_evidence_count: number;
    evidence_needs_strengthening_count: number;
    missing_evidence_count: number;
  };
}

export interface CompetencyRequirement {
  skill_type: string;
  element_id: string;
  element_name: string;
  importance: number | null;
  level: number | null;
  student_measurement_status: string;
  gap_status: string;
}

export interface GapAnalysis {
  technology_analysis: TechnologyGapAnalysis;

  competency_requirements:
    CompetencyRequirement[];

  interpretation: {
    strong_evidence: string;
    missing_evidence: string;
    not_assessed: string;
  };
}

export interface CareerGapAnalysisResponse {
  career_twin_id: string;
  snapshot_version: number;
  model_version: string;
  career: CareerInfo;
  gap_analysis: GapAnalysis;
}

export type CareerGpsActionType =
  | "STRENGTHEN_EVIDENCE"
  | "ASSESS_COMPETENCY"
  | "EXPLORE_MARKET_SIGNAL"
  | string;

export type CareerGpsPriority =
  | "HIGH"
  | "MEDIUM"
  | "LOW"
  | string;

export interface CareerGpsAction {
  action_type: CareerGpsActionType;

  technology?: string;
  competency?: string;

  priority: CareerGpsPriority;

  reason: string;
  recommended_action: string;

  current_evidence_confidence?: number | null;

  career_importance?: number | null;
  career_level?: number | null;

  sequence: number;
}

export interface CareerGpsSummary {
  total_actions: number;
  strengthen_evidence_actions: number;
  competency_assessment_actions: number;
  market_signal_exploration_actions: number;
}

export interface CareerGpsResponse {
  career_twin_id: string;
  snapshot_version: number;
  model_version: string;
  career: CareerInfo;

  career_gps: {
    actions: CareerGpsAction[];
    summary: CareerGpsSummary;
    methodology_status: string;
    interpretation: string;
  };
}

export interface MinimumActionPathItem
  extends CareerGpsAction {
  path_step: number;
  selection_reason: string;
}

export interface MinimumActionPathSummary {
  selected_action_count: number;
  available_gps_action_count: number;
}

export interface MinimumActionPathResponse {
  career_twin_id: string;
  snapshot_version: number;
  model_version: string;
  career: CareerInfo;

  minimum_action_path: {
    path: MinimumActionPathItem[];
    summary: MinimumActionPathSummary;
    methodology_status: string;
    optimization_status: string;
    interpretation: string;
  };
}

export interface SkillEvidenceSimulationRequest {
  simulation_type: "ADD_SKILL_EVIDENCE";
  skill_name: string;
  simulated_confidence: number;
}

export interface SimulationReadiness {
  interest_alignment: ReadinessMetric;
  technology_evidence_coverage: ReadinessMetric;
  technology_evidence_strength: ReadinessMetric;
  competency_measurement_coverage: ReadinessMetric;

  overall_readiness_score: number | null;
  overall_readiness_status: string;
  interpretation: string;
}

export interface SimulationState {
  skill_evidence_confidence: number | null;

  gap_analysis: {
    technology_analysis: TechnologyGapAnalysis;
    competency_requirements: CompetencyRequirement[];

    interpretation: {
      strong_evidence: string;
      missing_evidence: string;
      not_assessed: string;
    };
  };

  readiness: SimulationReadiness;
}

export interface SimulationCountChange {
  before: number;
  after: number;
}

export interface SimulationMetricChange {
  before: number | null;
  after: number | null;
  delta: number | null;
}

export interface CareerSimulationResponse {
  career_twin_id: string;
  snapshot_version: number;
  model_version: string;

  career: CareerInfo;

  simulation: {
    simulation_type: string;
    skill_name: string;

    before_evidence_confidence: number | null;
    after_evidence_confidence: number;

    database_mutated: boolean;
    interpretation: string;
  };

  before: SimulationState;
  after: SimulationState;

  delta: {
    technology_gap_changes: {
      strong_evidence_count: SimulationCountChange;

      evidence_needs_strengthening_count:
        SimulationCountChange;

      missing_evidence_count:
        SimulationCountChange;
    };

    readiness_changes: {
      technology_evidence_coverage:
        SimulationMetricChange;

      technology_evidence_strength:
        SimulationMetricChange;
    };

    interpretation: string;
  };

  database_mutated: boolean;
}

export async function getCareerReadiness(
  accessToken: string,
  careerId: string
): Promise<CareerReadinessResponse> {
  return apiRequest<CareerReadinessResponse>(
    `/acif/careers/${careerId}/readiness`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getCareerGapAnalysis(
  accessToken: string,
  careerId: string
): Promise<CareerGapAnalysisResponse> {
  return apiRequest<CareerGapAnalysisResponse>(
    `/acif/careers/${careerId}/gap-analysis`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getCareerGps(
  accessToken: string,
  careerId: string
): Promise<CareerGpsResponse> {
  return apiRequest<CareerGpsResponse>(
    `/acif/careers/${careerId}/career-gps`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getMinimumActionPath(
  accessToken: string,
  careerId: string
): Promise<MinimumActionPathResponse> {
  return apiRequest<MinimumActionPathResponse>(
    `/acif/careers/${careerId}/minimum-action-path`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function simulateCareerSkillEvidence(
  accessToken: string,
  careerId: string,
  payload: SkillEvidenceSimulationRequest
): Promise<CareerSimulationResponse> {
  return apiRequest<CareerSimulationResponse>(
    `/acif/careers/${careerId}/simulations/skill-evidence`,
    {
      method: "POST",
      accessToken,
      body: payload,
    }
  );
}