const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_number: number;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  file_sha256: string;
  extraction_status: string;
  parser_version: string;
  created_at: string;
}

export interface ResumeUploadResponse {
  resume_id: string;
  title: string;
  active_version_number: number;
  version: ResumeVersion;
}

export async function uploadResume(
  accessToken: string,
  file: File,
  title: string,
  resumeId?: string,
): Promise<ResumeUploadResponse> {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("title", title);

  if (resumeId) {
    formData.append("resume_id", resumeId);
  }

  const response = await fetch(
    `${API_BASE_URL}/resumes/upload`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
    },
  );

  const contentType = response.headers.get("content-type");

  const data = contentType?.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    let message = "Resume upload failed.";

    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data
    ) {
      const detail = (data as { detail?: unknown }).detail;

      if (typeof detail === "string") {
        message = detail;
      }
    }

    throw new Error(message);
  }

  return data as ResumeUploadResponse;
}