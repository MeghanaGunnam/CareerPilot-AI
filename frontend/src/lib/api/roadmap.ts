import { apiRequest } from "@/lib/api/client";

export type RoadmapStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "SKIPPED";

export interface RoadmapItem {
  id: string;
  item_key: string;
  provenance: string;
  current_evidence_state: string;
  reason: string;
  recommended_action: string;
  evidence_building_action: string;
  milestone: string;
  status: RoadmapStatus;
  order: number;
  model_version: string;
  snapshot_version: number;
}

export interface RoadmapResponse {
  career_goal_id: string;
  target_role: string;
  career_id: string;
  items: RoadmapItem[];
}

export function getRoadmap(accessToken: string) {
  return apiRequest<RoadmapResponse>("/roadmap", {
    accessToken,
  });
}

export function updateRoadmapItemStatus(
  accessToken: string,
  itemId: string,
  status: RoadmapStatus,
) {
  return apiRequest<RoadmapItem>(`/roadmap/${itemId}`, {
    method: "PATCH",
    accessToken,
    body: { status },
  });
}
