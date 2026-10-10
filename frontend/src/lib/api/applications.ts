import { apiRequest } from "@/lib/api/client";

export const APPLICATION_STATUSES = ["SAVED", "APPLIED", "ASSESSMENT", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"] as const;
export type ApplicationStatus = typeof APPLICATION_STATUSES[number];
export interface ApplicationInput {
  company: string;
  job_title: string;
  location: string | null;
  employment_type: string | null;
  job_url: string | null;
  jd_analysis_id: string | null;
  applied_date: string | null;
  status: ApplicationStatus;
  notes: string | null;
}
export interface ApplicationRecord extends ApplicationInput { id: string; created_at: string; updated_at: string }
export interface ApplicationList { items: ApplicationRecord[]; total: number; limit: number; offset: number }
export const listApplications = (accessToken: string, offset: number, status: string, signal?: AbortSignal) => apiRequest<ApplicationList>(`/applications?limit=10&offset=${offset}${status ? `&status=${encodeURIComponent(status)}` : ""}`, { accessToken, signal, cache: "no-store" });
export const getApplication = (accessToken: string, id: string, signal?: AbortSignal) => apiRequest<ApplicationRecord>(`/applications/${encodeURIComponent(id)}`, { accessToken, signal, cache: "no-store" });
export const saveApplication = (accessToken: string, body: ApplicationInput, id?: string, signal?: AbortSignal) => apiRequest<ApplicationRecord>(id ? `/applications/${encodeURIComponent(id)}` : "/applications", { method: id ? "PATCH" : "POST", body, accessToken, signal });
export const deleteApplication = (accessToken: string, id: string, signal?: AbortSignal) => apiRequest<void>(`/applications/${encodeURIComponent(id)}`, { method: "DELETE", accessToken, signal });
