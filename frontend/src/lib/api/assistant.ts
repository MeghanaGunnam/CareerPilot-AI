import { apiRequest } from "@/lib/api/client";

export type AssistantTopic = "auto" | "next_steps" | "skills" | "profile" | "assessments" | "certifications" | "job_match" | "applications" | "progress";
export interface AssistantStatus {
  provider_status: "READY" | "ASSISTANT_NOT_CONFIGURED" | "CONSENT_REQUIRED" | "PROVIDER_UNAVAILABLE";
  mode: "STRUCTURED_GROUNDING";
  generation_mode: "CONSTRAINED_SOURCE_SELECTION";
  message: string;
}
export interface AssistantSource {
  id: string;
  kind: "FACT" | "MODEL_OUTPUT" | "PERSONALIZED_RECOMMENDATION";
  text: string;
  provenance: string;
  href: "/profile" | "/assessment" | "/roadmap" | "/certifications" | "/job-match" | "/applications" | "/progress" | "/evidence" | "/dashboard";
}
export interface AssistantResponse extends AssistantStatus {
  answer: string | null;
  grounding_status: "GROUNDED_SELECTION" | "INSUFFICIENT_CONTEXT" | "UNAVAILABLE";
  topic: AssistantTopic;
  context_sources: AssistantSource[];
  recommended_actions: AssistantSource[];
  limitations: string[];
  explanation_provenance: "LLM_EXPLANATION_SELECTION" | "NO_GENERATION";
}
export interface AssistantRequest {
  message: string;
  topic: AssistantTopic;
  jd_analysis_id: string | null;
  application_id: string | null;
  allow_provider_processing: boolean;
}
export const getAssistantStatus = (accessToken: string, signal?: AbortSignal) => apiRequest<AssistantStatus>("/assistant/status", { accessToken, signal, cache: "no-store" });
export const askAssistant = (accessToken: string, body: AssistantRequest, signal?: AbortSignal) => apiRequest<AssistantResponse>("/assistant/chat", { method: "POST", accessToken, body, signal });
