"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getCurrentUser,
  logout,
  type User,
} from "@/lib/api/auth";
import {
  getPrimaryCareerGoal,
  getStudentProfile,
  getEducations,
  getExperiences,
  getProjects,
  getCertifications,
  type CareerGoal,
  type StudentProfile,
  type Education,
  type Experience,
  type Project,
  type Certification,
} from "@/lib/api/students";
import {
  resolveCareerByOnetCode,
} from "@/lib/api/careers";

import {
  getCareerReadiness,
  getCareerGapAnalysis,
  getCareerGps,
  getMinimumActionPath,
  type CareerReadinessResponse,
  type CareerGapAnalysisResponse,
  type CareerGpsResponse,
  type MinimumActionPathResponse,
  type ReadinessMetric,
} from "@/lib/api/acif";

import WhatIfSimulator from "./WhatIfSimulator";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";
const REFRESH_TOKEN_KEY = "careerpilot_refresh_token";



function formatPercent(value: number | null) {
  if (value === null) {
    return "Not available";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function formatConfidence(value?: number | null) {
  if (value === null || value === undefined) {
    return "No measured confidence";
  }

  return `${(value * 100).toFixed(1)}% evidence confidence`;
}

function ReadinessCard({
  title,
  metric,
  description,
}: {
  title: string;
  metric: ReadinessMetric;
  description: string;
}) {
  const percentage =
    metric.score !== null
      ? Math.max(
          0,
          Math.min(100, metric.score * 100),
        )
      : 0;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {title}
          </p>

          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">
            {formatPercent(metric.score)}
          </p>
        </div>

        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
          {metric.status}
        </span>
      </div>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-blue-600 transition-all"
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-600">
        {description}
      </p>
    </article>
  );
}
function ProfileSummaryCard({
  label,
  count,
  detail,
}: {
  label: string;
  count: number;
  detail: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-900">
          {label}
        </p>

        <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-blue-100 px-2 text-xs font-bold text-blue-700">
          {count}
        </span>
      </div>

      <p className="mt-3 line-clamp-2 text-xs leading-5 text-slate-500">
        {detail}
      </p>
    </article>
  );
}
export default function DashboardPage() {
  const router = useRouter();

  const [user, setUser] =
    useState<User | null>(null);
  const [primaryCareerGoal, setPrimaryCareerGoal] =
  useState<CareerGoal | null>(null);
  const [resolvedCareerId, setResolvedCareerId] =
    useState<string | null>(null);
  const [studentProfile, setStudentProfile] =
  useState<StudentProfile | null>(null);

  const [educations, setEducations] =
  useState<Education[]>([]);

  const [experiences, setExperiences] =
  useState<Experience[]>([]);

  const [projects, setProjects] =
  useState<Project[]>([]);

  const [certifications, setCertifications] =
  useState<Certification[]>([]);
  const [readiness, setReadiness] =
    useState<CareerReadinessResponse | null>(null);

  const [gapAnalysis, setGapAnalysis] =
    useState<CareerGapAnalysisResponse | null>(null);

  const [careerGps, setCareerGps] =
    useState<CareerGpsResponse | null>(null);

  const [minimumPath, setMinimumPath] =
    useState<MinimumActionPathResponse | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);
  const [careerTwinMissing, setCareerTwinMissing] =
  useState(false);
  useEffect(() => {
    async function loadDashboard() {
      const accessToken =
        sessionStorage.getItem(ACCESS_TOKEN_KEY);

      if (!accessToken) {
        router.replace("/login");
        return;
      }

      try {
        const [
  currentUser,
  primaryGoal,
  educationsResponse,
  experiencesResponse,
  projectsResponse,
  certificationsResponse,
] = await Promise.all([
  getCurrentUser(accessToken),
  getPrimaryCareerGoal(accessToken),
  getEducations(accessToken),
  getExperiences(accessToken),
  getProjects(accessToken),
  getCertifications(accessToken),
]);

let profileResponse: StudentProfile | null = null;

try {
  profileResponse =
    await getStudentProfile(accessToken);
} catch {
  profileResponse = null;
}

if (!primaryGoal.onet_soc_code) {
  throw new Error(
    "Your primary career goal does not have an O*NET occupation mapping."
  );
}

const targetCareer = await resolveCareerByOnetCode(
  primaryGoal.target_role,
  primaryGoal.onet_soc_code
);

const careerId = targetCareer.id;

        const [
          readinessResponse,
          gapResponse,
          gpsResponse,
          minimumPathResponse,
        ] = await Promise.all([
          getCareerReadiness(
            accessToken,
            careerId,
          ),

          getCareerGapAnalysis(
            accessToken,
            careerId,
          ),

          getCareerGps(
            accessToken,
            careerId,
          ),

          getMinimumActionPath(
            accessToken,
            careerId,
          ),
        ]);

setUser(currentUser);
setStudentProfile(profileResponse);
setEducations(educationsResponse);
setExperiences(experiencesResponse);
setProjects(projectsResponse);
setCertifications(certificationsResponse);

setResolvedCareerId(careerId);
setReadiness(readinessResponse);
setGapAnalysis(gapResponse);
setCareerGps(gpsResponse);
setMinimumPath(minimumPathResponse);
setPrimaryCareerGoal(primaryGoal);
      } catch (err) {
  const message =
    err instanceof Error
      ? err.message
      : "Unable to load your career intelligence dashboard.";

  if (
    message
      .toLowerCase()
      .includes("career twin has not been created yet")
  ) {
    setCareerTwinMissing(true);
    setError(null);
  } else {
    console.error(
      "Dashboard loading failed:",
      err,
    );

    setError(message);
  }
} finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, [router]);

  async function handleLogout() {
    const accessToken =
      sessionStorage.getItem(ACCESS_TOKEN_KEY);

    const refreshToken =
      sessionStorage.getItem(REFRESH_TOKEN_KEY);

    try {
      if (accessToken && refreshToken) {
        await logout(
          accessToken,
          refreshToken,
        );
      }
    } catch (error) {
      console.error(
        "Logout request failed:",
        error,
      );
    } finally {
      sessionStorage.removeItem(
        ACCESS_TOKEN_KEY,
      );

      sessionStorage.removeItem(
        REFRESH_TOKEN_KEY,
      );

      router.replace("/login");
    }
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

          <p className="mt-4 text-sm text-slate-600">
            Building your Career Intelligence
            Dashboard...
          </p>
        </div>
      </main>
    );
  }
  if (careerTwinMissing) {
  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-xl font-bold text-slate-950">
              CareerPilot AI
            </p>

            <p className="text-xs text-slate-500">
              Adaptive Career Intelligence
            </p>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-16">
        <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm sm:p-10">
          <div className="inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-blue-700">
            Career Twin setup
          </div>

          <h1 className="mt-5 text-3xl font-bold tracking-tight text-slate-950">
            Build your Career Twin
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
            Your Career Twin has not been created yet. Complete
            your initial career interest assessment so CareerPilot
            can create your first evidence-aware snapshot and begin
            generating personalized career intelligence.
          </p>

          <div className="mt-8 rounded-2xl bg-slate-50 p-6">
            <p className="text-sm font-semibold text-slate-950">
              Start with Career Interests
            </p>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              Your responses establish the interest component of
              your Career Twin. Resume evidence, assessments, and
              other verified evidence can strengthen the Twin as
              you continue using CareerPilot.
            </p>

            <button
              type="button"
              onClick={() =>
                router.push("/assessment/riasec")
              }
              className="mt-5 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              Complete Career Interest Assessment
            </button>
          </div>

          <p className="mt-6 text-xs leading-5 text-slate-500">
            CareerPilot separates interest alignment, skill
            evidence, competency measurements, and occupational
            signals. These indicators do not predict employment,
            placement, or career success.
          </p>
        </section>
      </div>
    </main>
  );
}
  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="w-full max-w-lg rounded-2xl border border-red-200 bg-white p-8 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wider text-red-600">
            Dashboard error
          </p>

          <h1 className="mt-2 text-2xl font-semibold text-slate-950">
            Career intelligence could not be loaded
          </h1>

          <p className="mt-4 text-sm leading-6 text-slate-600">
            {error}
          </p>

          <button
            type="button"
            onClick={() =>
              window.location.reload()
            }
            className="mt-6 rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            Try Again
          </button>
        </div>
      </main>
    );
  }

  if (
  !user ||
  !primaryCareerGoal ||
  !resolvedCareerId ||
  !readiness ||
  !gapAnalysis ||
  !careerGps ||
  !minimumPath
) {
  return null;
}

  const readinessData = readiness.readiness;

  const technologyAnalysis =
    gapAnalysis.gap_analysis.technology_analysis;

  const strongEvidence =
    technologyAnalysis.strong_evidence;

  const evidenceNeedsStrengthening =
    technologyAnalysis.evidence_needs_strengthening;

  const missingEvidence =
    technologyAnalysis.missing_evidence;

  const competencyRequirements =
    gapAnalysis.gap_analysis.competency_requirements;

  const unassessedCompetencies =
    competencyRequirements.filter(
      (item) =>
        item.student_measurement_status ===
        "NOT_ASSESSED",
    );

  const gps = careerGps.career_gps;

  const path =
    minimumPath.minimum_action_path;

  const simulationTechnologies = [
    ...strongEvidence,
    ...evidenceNeedsStrengthening,
    ...missingEvidence,
  ];

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-5 py-4 sm:px-6 lg:px-8">
          <button
            type="button"
            onClick={() =>
              router.push("/dashboard")
            }
            className="text-left"
          >
            <p className="text-xl font-bold tracking-tight text-slate-950">
              CareerPilot AI
            </p>

            <p className="text-xs text-slate-500">
              Adaptive Career Intelligence
            </p>
          </button>

          <div className="flex items-center gap-2">
  <nav className="hidden items-center gap-1 lg:flex">
  <button
    type="button"
    onClick={() => router.push("/dashboard")}
    className="rounded-lg bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-100"
  >
    Dashboard
  </button>

  <button
    type="button"
    onClick={() => router.push("/profile")}
    className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
  >
    Profile
  </button>

  <button
    type="button"
    onClick={() => router.push("/resume")}
    className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
  >
    Resume
  </button>

  <button
    type="button"
    onClick={() => router.push("/skills")}
    className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
  >
    Skills & Evidence
  </button>

  <button
    type="button"
    onClick={() => router.push("/assessment")}
    className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-950"
  >
    Assessments
  </button>
</nav>
  <div className="hidden text-right xl:block">
              <p className="text-sm font-medium text-slate-800">
                {user.email}
              </p>

              <p className="text-xs text-slate-500">
                {user.is_verified
                  ? "Verified account"
                  : "Email verification pending"}
              </p>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-6 lg:px-8 lg:py-10">
        <section className="overflow-hidden rounded-3xl bg-slate-950 p-7 text-white shadow-sm sm:p-9">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-300">
                Career Intelligence Dashboard
              </p>

              <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
                {primaryCareerGoal.target_role}
              </h1>

              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                CareerPilot uses your Career Twin,
                evidence, interests, and occupational
                signals to explain where your current
                profile aligns and what evidence you can
                strengthen next.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 lg:min-w-80">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                O*NET occupational anchor
              </p>

              <p className="mt-2 text-lg font-semibold">
                {readiness.career.title}
              </p>

              <p className="mt-1 text-sm text-slate-300">
                {readiness.career.onet_soc_code}
                {" · "}
                Job Zone{" "}
                {readiness.career.job_zone ?? "N/A"}
              </p>

              <p className="mt-3 text-xs leading-5 text-slate-400">
                O*NET {readiness.career.onet_version}
                {" · "}
                CareerPilot role mapping
              </p>
            </div>
          </div>
                    </section>

          <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                  Profile Overview
                </p>

                <h2 className="mt-2 text-2xl font-bold text-slate-950">
                  {studentProfile?.full_name ||
                    "Your Career Profile"}
                </h2>

                {studentProfile?.headline && (
                  <p className="mt-2 text-sm text-slate-600">
                    {studentProfile.headline}
                  </p>
                )}
              </div>

              <button
                type="button"
                onClick={() => router.push("/profile")}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Manage Profile
              </button>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <ProfileSummaryCard
                label="Education"
                count={educations.length}
                detail={
                  educations[0]
                    ? `${educations[0].degree} · ${educations[0].institution_name}`
                    : "Add your academic background"
                }
              />

              <ProfileSummaryCard
                label="Experience"
                count={experiences.length}
                detail={
                  experiences[0]
                    ? `${experiences[0].job_title} · ${experiences[0].company_name}`
                    : "Add internships or work experience"
                }
              />

              <ProfileSummaryCard
                label="Projects"
                count={projects.length}
                detail={
                  projects[0]
                    ? projects[0].title
                    : "Add evidence-building projects"
                }
              />

              <ProfileSummaryCard
                label="Certifications"
                count={certifications.length}
                detail={
                  certifications[0]
                    ? certifications[0].name
                    : "Add relevant certifications"
                }
              />
            </div>
          </section>

          <section className="mt-8">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                ACIF Readiness Dimensions
              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
                Your current career evidence
              </h2>
            </div>

            <div className="text-sm text-slate-500">
              Career Twin snapshot{" "}
              {readiness.snapshot_version}
              {" · "}
              {readiness.model_version}
            </div>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <ReadinessCard
              title="Interest Alignment"
              metric={
                readinessData.interest_alignment
              }
              description="Alignment between your current RIASEC interest profile and the occupational interest profile."
            />

            <ReadinessCard
              title="Technology Evidence Coverage"
              metric={
                readinessData
                  .technology_evidence_coverage
              }
              description={`${readinessData.technology_evidence_coverage.weak_evidence_count ?? 0} of ${readinessData.technology_evidence_coverage.total_market_signals ?? 0} market technology signals currently have supporting evidence.`}
            />

            <ReadinessCard
              title="Evidence Strength"
              metric={
                readinessData
                  .technology_evidence_strength
              }
              description="Average ACIF evidence confidence across technologies for which supporting evidence was found."
            />

            <ReadinessCard
              title="Competency Measurement Coverage"
              metric={
                readinessData
                  .competency_measurement_coverage
              }
              description={`${readinessData.competency_measurement_coverage.measured_competency_count ?? 0} of ${readinessData.competency_measurement_coverage.total_competency_count ?? 0} occupational competencies currently have student measurements.`}
            />
          </div>

          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4">
            <p className="text-sm font-semibold text-amber-900">
              Overall readiness is not calibrated
            </p>

            <p className="mt-1 text-sm leading-6 text-amber-800">
              {readinessData.interpretation}
            </p>
          </div>
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                  Evidence Map
                </p>

                <h2 className="mt-2 text-2xl font-bold text-slate-950">
                  Technology evidence
                </h2>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                {
                  readinessData
                    .technology_evidence_coverage
                    .total_market_signals
                }{" "}
                signals
              </span>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-emerald-50 p-4">
                <p className="text-2xl font-bold text-emerald-700">
                  {strongEvidence.length}
                </p>

                <p className="mt-1 text-xs font-medium text-emerald-800">
                  Strong evidence
                </p>
              </div>

              <div className="rounded-xl bg-amber-50 p-4">
                <p className="text-2xl font-bold text-amber-700">
                  {
                    evidenceNeedsStrengthening.length
                  }
                </p>

                <p className="mt-1 text-xs font-medium text-amber-800">
                  Strengthen
                </p>
              </div>

              <div className="rounded-xl bg-slate-100 p-4">
                <p className="text-2xl font-bold text-slate-700">
                  {missingEvidence.length}
                </p>

                <p className="mt-1 text-xs font-medium text-slate-600">
                  Missing evidence
                </p>
              </div>
            </div>

            <div className="mt-7">
              <h3 className="text-sm font-semibold text-slate-950">
                Evidence that needs strengthening
              </h3>

              <div className="mt-3 space-y-3">
                {evidenceNeedsStrengthening.map(
                  (item) => (
                    <div
                      key={
                        item.normalized_technology
                      }
                      className="rounded-xl border border-slate-200 p-4"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="font-semibold text-slate-900">
                            {item.technology}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            Evidence:{" "}
                            {item.evidence_families?.join(
                              " + ",
                            ) || "Available"}
                          </p>
                        </div>

                        <span className="w-fit rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                          {formatConfidence(
                            item.evidence_confidence,
                          )}
                        </span>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>

            <div className="mt-7">
              <h3 className="text-sm font-semibold text-slate-950">
                Market signals with no current evidence
              </h3>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                Missing evidence does not mean you lack
                the skill. CareerPilot simply has not
                found supporting evidence in the current
                Career Twin.
              </p>

              <div className="mt-4 flex flex-wrap gap-2">
                {missingEvidence.map((item) => (
                  <span
                    key={
                      item.normalized_technology
                    }
                    className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700"
                  >
                    {item.technology}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
              Minimum Action Path
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              What to strengthen next
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              ACIF selected{" "}
              {path.summary.selected_action_count}{" "}
              high-priority actions from{" "}
              {
                path.summary
                  .available_gps_action_count
              }{" "}
              available Career GPS actions.
            </p>

            <div className="mt-6 space-y-4">
              {path.path.map((item) => (
                <div
                  key={item.path_step}
                  className="relative rounded-2xl border border-slate-200 p-5"
                >
                  <div className="flex gap-4">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                      {item.path_step}
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-slate-950">
                          {item.technology ??
                            item.competency ??
                            "Career action"}
                        </h3>

                        <span className="rounded-full bg-red-50 px-2.5 py-1 text-[11px] font-semibold text-red-700">
                          {item.priority}
                        </span>
                      </div>

                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        {item.recommended_action}
                      </p>

                      {item.current_evidence_confidence !==
                        undefined &&
                        item.current_evidence_confidence !==
                          null && (
                          <p className="mt-3 text-xs font-medium text-slate-500">
                            Current evidence confidence:{" "}
                            {formatPercent(
                              item.current_evidence_confidence,
                            )}
                          </p>
                        )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Methodology
              </p>

              <p className="mt-2 text-sm font-medium text-slate-800">
                {path.methodology_status}
                {" · "}
                {path.optimization_status}
              </p>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                This is a deterministic V1 shortlist,
                not a mathematically optimized learning
                path.
              </p>
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                  Career GPS
                </p>

                <h2 className="mt-2 text-2xl font-bold text-slate-950">
                  Adaptive next steps
                </h2>
              </div>

              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                {gps.summary.total_actions} actions
              </span>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-2xl font-bold text-slate-950">
                  {
                    gps.summary
                      .strengthen_evidence_actions
                  }
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Strengthen evidence
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-2xl font-bold text-slate-950">
                  {
                    gps.summary
                      .competency_assessment_actions
                  }
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Assess competencies
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 p-4">
                <p className="text-2xl font-bold text-slate-950">
                  {
                    gps.summary
                      .market_signal_exploration_actions
                  }
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Explore signals
                </p>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              {gps.actions
                .slice(0, 5)
                .map((action) => (
                  <div
                    key={action.sequence}
                    className="rounded-xl border border-slate-200 p-4"
                  >
                    <div className="flex items-start gap-3">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-700">
                        {action.sequence}
                      </span>

                      <div>
                        <p className="text-sm font-semibold text-slate-900">
                          {action.technology ??
                            action.competency ??
                            action.action_type}
                        </p>

                        <p className="mt-1 text-xs leading-5 text-slate-500">
                          {action.reason}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
            </div>

            <p className="mt-5 text-xs leading-5 text-slate-500">
              {gps.interpretation}
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
              Competency Measurement
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              What CareerPilot still needs to measure
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              O*NET describes occupational competency
              requirements, but CareerPilot currently
              has measurements for{" "}
              {
                readinessData
                  .competency_measurement_coverage
                  .measured_competency_count
              }{" "}
              of{" "}
              {
                readinessData
                  .competency_measurement_coverage
                  .total_competency_count
              }{" "}
              competencies.
            </p>

            <div className="mt-6 space-y-3">
              {unassessedCompetencies
                .slice(0, 5)
                .map((competency) => (
                  <div
                    key={competency.element_id}
                    className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 p-4"
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-900">
                        {competency.element_name}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {competency.skill_type}
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="text-xs font-medium text-slate-500">
                        O*NET importance
                      </p>

                      <p className="mt-1 text-sm font-semibold text-slate-900">
                        {competency.importance ??
                          "N/A"}
                      </p>
                    </div>
                  </div>
                ))}
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                onClick={() =>
                  router.push(
                    "/assessment/riasec",
                  )
                }
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Review Career Interest Assessment
              </button>

              <button
                type="button"
                onClick={() =>
                  router.push("/assessment")
                }
                className="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Technical Assessments
              </button>
            </div>
          </div>
        </section>

        <WhatIfSimulator
          careerId={resolvedCareerId}
          technologies={simulationTechnologies}
        />

        <section className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
          <div className="grid gap-6 md:grid-cols-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Career Twin
              </p>

              <p className="mt-2 text-sm font-semibold text-slate-900">
                Snapshot {readiness.snapshot_version}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Evidence-aware student state
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Intelligence Model
              </p>

              <p className="mt-2 text-sm font-semibold text-slate-900">
                {readiness.model_version}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Adaptive Career Intelligence
                Framework
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Occupational Data
              </p>

              <p className="mt-2 text-sm font-semibold text-slate-900">
                O*NET {readiness.career.onet_version}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {readiness.career.onet_soc_code}
              </p>
            </div>
          </div>
        </section>

        <footer className="py-10 text-center">
          <p className="text-xs leading-5 text-slate-500">
            CareerPilot AI provides evidence-based
            career decision support. Interest alignment,
            evidence coverage, and evidence confidence
            are separate indicators and do not predict
            employment, placement, or career success.
          </p>
        </footer>
      </div>
    </main>
  );
}