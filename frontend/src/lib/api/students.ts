import { apiRequest } from "./client";

/* =========================================================
   Shared
========================================================= */

export interface BaseRecord {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

/* =========================================================
   Student Profile
========================================================= */

export interface StudentProfile extends BaseRecord {
  full_name: string;
  phone: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  headline: string | null;
  bio: string | null;
}

export interface StudentProfileData {
  full_name: string;
  phone?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  headline?: string | null;
  bio?: string | null;
}

export async function createStudentProfile(
  accessToken: string,
  data: StudentProfileData
): Promise<StudentProfile> {
  return apiRequest<StudentProfile>(
    "/students/profile",
    {
      method: "POST",
      accessToken,
      body: data,
    }
  );
}

export async function getStudentProfile(
  accessToken: string
): Promise<StudentProfile> {
  return apiRequest<StudentProfile>(
    "/students/profile",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function updateStudentProfile(
  accessToken: string,
  data: Partial<StudentProfileData>
): Promise<StudentProfile> {
  return apiRequest<StudentProfile>(
    "/students/profile",
    {
      method: "PATCH",
      accessToken,
      body: data,
    }
  );
}

/* =========================================================
   Education
========================================================= */

export interface Education extends BaseRecord {
  institution_name: string;
  degree: string;
  field_of_study: string | null;
  start_year: number | null;
  end_year: number | null;
  grade: string | null;
}

export interface EducationData {
  institution_name: string;
  degree: string;
  field_of_study?: string | null;
  start_year?: number | null;
  end_year?: number | null;
  grade?: string | null;
}

export async function createEducation(
  accessToken: string,
  data: EducationData
): Promise<Education> {
  return apiRequest<Education>(
    "/students/education",
    {
      method: "POST",
      accessToken,
      body: data,
    }
  );
}

export async function getEducations(
  accessToken: string
): Promise<Education[]> {
  return apiRequest<Education[]>(
    "/students/education",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getEducation(
  accessToken: string,
  educationId: string
): Promise<Education> {
  return apiRequest<Education>(
    `/students/education/${educationId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function updateEducation(
  accessToken: string,
  educationId: string,
  data: Partial<EducationData>
): Promise<Education> {
  return apiRequest<Education>(
    `/students/education/${educationId}`,
    {
      method: "PATCH",
      accessToken,
      body: data,
    }
  );
}

export async function deleteEducation(
  accessToken: string,
  educationId: string
): Promise<void> {
  return apiRequest<void>(
    `/students/education/${educationId}`,
    {
      method: "DELETE",
      accessToken,
    }
  );
}

/* =========================================================
   Experience
========================================================= */

export interface Experience extends BaseRecord {
  company_name: string;
  job_title: string;
  employment_type: string | null;
  location: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
}

export interface ExperienceData {
  company_name: string;
  job_title: string;
  employment_type?: string | null;
  location?: string | null;
  start_date: string;
  end_date?: string | null;
  is_current?: boolean;
  description?: string | null;
}

export async function createExperience(
  accessToken: string,
  data: ExperienceData
): Promise<Experience> {
  return apiRequest<Experience>(
    "/students/experiences",
    {
      method: "POST",
      accessToken,
      body: data,
    }
  );
}

export async function getExperiences(
  accessToken: string
): Promise<Experience[]> {
  return apiRequest<Experience[]>(
    "/students/experiences",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getExperience(
  accessToken: string,
  experienceId: string
): Promise<Experience> {
  return apiRequest<Experience>(
    `/students/experiences/${experienceId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function updateExperience(
  accessToken: string,
  experienceId: string,
  data: Partial<ExperienceData>
): Promise<Experience> {
  return apiRequest<Experience>(
    `/students/experiences/${experienceId}`,
    {
      method: "PATCH",
      accessToken,
      body: data,
    }
  );
}

export async function deleteExperience(
  accessToken: string,
  experienceId: string
): Promise<void> {
  return apiRequest<void>(
    `/students/experiences/${experienceId}`,
    {
      method: "DELETE",
      accessToken,
    }
  );
}

/* =========================================================
   Projects
========================================================= */

export interface Project extends BaseRecord {
  title: string;
  description: string | null;
  role: string | null;
  technologies: string | null;
  project_url: string | null;
  repository_url: string | null;
  start_date: string | null;
  end_date: string | null;
  is_ongoing: boolean;
}

export interface ProjectData {
  title: string;
  description?: string | null;
  role?: string | null;
  technologies?: string | null;
  project_url?: string | null;
  repository_url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_ongoing?: boolean;
}

export async function createProject(
  accessToken: string,
  data: ProjectData
): Promise<Project> {
  return apiRequest<Project>(
    "/students/projects",
    {
      method: "POST",
      accessToken,
      body: data,
    }
  );
}

export async function getProjects(
  accessToken: string
): Promise<Project[]> {
  return apiRequest<Project[]>(
    "/students/projects",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getProject(
  accessToken: string,
  projectId: string
): Promise<Project> {
  return apiRequest<Project>(
    `/students/projects/${projectId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function updateProject(
  accessToken: string,
  projectId: string,
  data: Partial<ProjectData>
): Promise<Project> {
  return apiRequest<Project>(
    `/students/projects/${projectId}`,
    {
      method: "PATCH",
      accessToken,
      body: data,
    }
  );
}

export async function deleteProject(
  accessToken: string,
  projectId: string
): Promise<void> {
  return apiRequest<void>(
    `/students/projects/${projectId}`,
    {
      method: "DELETE",
      accessToken,
    }
  );
}

/* =========================================================
   Certifications
========================================================= */

export interface Certification extends BaseRecord {
  name: string;
  issuing_organization: string;
  issue_date: string | null;
  expiration_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
  description: string | null;
}

export interface CertificationData {
  name: string;
  issuing_organization: string;
  issue_date?: string | null;
  expiration_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
  description?: string | null;
}

export async function createCertification(
  accessToken: string,
  data: CertificationData
): Promise<Certification> {
  return apiRequest<Certification>(
    "/students/certifications",
    {
      method: "POST",
      accessToken,
      body: data,
    }
  );
}

export async function getCertifications(
  accessToken: string
): Promise<Certification[]> {
  return apiRequest<Certification[]>(
    "/students/certifications",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getCertification(
  accessToken: string,
  certificationId: string
): Promise<Certification> {
  return apiRequest<Certification>(
    `/students/certifications/${certificationId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function updateCertification(
  accessToken: string,
  certificationId: string,
  data: Partial<CertificationData>
): Promise<Certification> {
  return apiRequest<Certification>(
    `/students/certifications/${certificationId}`,
    {
      method: "PATCH",
      accessToken,
      body: data,
    }
  );
}

export async function deleteCertification(
  accessToken: string,
  certificationId: string
): Promise<void> {
  return apiRequest<void>(
    `/students/certifications/${certificationId}`,
    {
      method: "DELETE",
      accessToken,
    }
  );
}

/* =========================================================
   Career Goals
========================================================= */

export interface CareerGoal extends BaseRecord {
  target_role: string;
  target_industry: string | null;
  target_location: string | null;
  employment_type: string | null;
  target_timeline_months: number | null;
  priority: number;
  is_active: boolean;
  notes: string | null;
}

export interface CareerGoalData {
  target_role: string;
  target_industry?: string | null;
  target_location?: string | null;
  employment_type?: string | null;
  target_timeline_months?: number | null;
  priority?: number;
  is_active?: boolean;
  notes?: string | null;
}

export async function createCareerGoal(
  accessToken: string,
  data: CareerGoalData
): Promise<CareerGoal> {
  return apiRequest<CareerGoal>(
    "/students/career-goals",
    {
      method: "POST",
      accessToken,
      body: data,
    }
  );
}

export async function getCareerGoals(
  accessToken: string
): Promise<CareerGoal[]> {
  return apiRequest<CareerGoal[]>(
    "/students/career-goals",
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function getCareerGoal(
  accessToken: string,
  careerGoalId: string
): Promise<CareerGoal> {
  return apiRequest<CareerGoal>(
    `/students/career-goals/${careerGoalId}`,
    {
      method: "GET",
      accessToken,
    }
  );
}

export async function updateCareerGoal(
  accessToken: string,
  careerGoalId: string,
  data: Partial<CareerGoalData>
): Promise<CareerGoal> {
  return apiRequest<CareerGoal>(
    `/students/career-goals/${careerGoalId}`,
    {
      method: "PATCH",
      accessToken,
      body: data,
    }
  );
}

export async function deleteCareerGoal(
  accessToken: string,
  careerGoalId: string
): Promise<void> {
  return apiRequest<void>(
    `/students/career-goals/${careerGoalId}`,
    {
      method: "DELETE",
      accessToken,
    }
  );
}