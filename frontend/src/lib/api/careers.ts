import { apiRequest } from "@/lib/api/client";

export interface Career {
  id: string;
  onet_soc_code: string;
  title: string;
  description: string | null;
  job_zone: number | null;
  onet_version: string;
}

export async function searchCareers(
  search: string,
  limit = 10,
): Promise<Career[]> {
  const params = new URLSearchParams({
    search,
    limit: String(limit),
    offset: "0",
  });

  return apiRequest<Career[]>(
    `/careers?${params.toString()}`,
    {
      method: "GET",
    },
  );
}

export async function resolveCareerByOnetCode(
  _search: string,
  onetSocCode: string,
): Promise<Career> {
  const normalizedCode = onetSocCode.trim();

  const careers = await searchCareers(
    normalizedCode,
    20,
  );

  const career = careers.find(
    (item) =>
      item.onet_soc_code.trim() === normalizedCode,
  );

  if (!career) {
    throw new Error(
      `Career with O*NET-SOC code ${normalizedCode} could not be resolved.`,
    );
  }

  return career;
}