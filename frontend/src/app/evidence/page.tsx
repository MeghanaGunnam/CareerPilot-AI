"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getMySkills,
  MySkillsResponse,
  StudentSkill,
} from "@/lib/api/skills";

import {
  ResumeUploadResponse,
  uploadResume,
} from "@/lib/api/resumes";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";
const REFRESH_TOKEN_KEY = "careerpilot_refresh_token";

function formatPercent(value: number | null) {
  if (value === null) {
    return "Not measured";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatLabel(value: string | null | undefined) {
  if (!value) {
    return "Unknown";
  }

  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function Metric({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </div>
  );
}

function SkillCard({ skill }: { skill: StudentSkill }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="flex w-full items-start justify-between gap-5 p-5 text-left transition hover:bg-slate-50"
      >
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-slate-950">
              {skill.canonical_name}
            </h3>

            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
              {skill.evidence.length} evidence
            </span>
          </div>

          <p className="mt-2 text-sm text-slate-500">
            {skill.category ?? "Skill category not assigned"}
          </p>
        </div>

        <span className="shrink-0 text-sm font-medium text-indigo-700">
          {expanded ? "Hide evidence" : "View evidence"}
        </span>
      </button>

      <div className="grid gap-3 border-t border-slate-100 bg-slate-50/70 p-5 sm:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Evidence confidence
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {formatPercent(skill.evidence_confidence)}
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Estimated proficiency
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {formatPercent(skill.estimated_proficiency)}
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Freshness
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-900">
            {formatPercent(skill.freshness_score)}
          </p>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-200 p-5">
          <div className="mb-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-sm leading-6 text-indigo-950">
              Resume mentions provide evidence that this skill appears in your
              career profile. They do not by themselves prove technical
              proficiency.
            </p>
          </div>

          <div className="space-y-3">
            {skill.evidence.map((evidence) => (
              <div
                key={evidence.id}
                className="rounded-xl border border-slate-200 p-4"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700">
                    {formatLabel(evidence.source_type)}
                  </span>

                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                    {formatLabel(evidence.evidence_status)}
                  </span>

                  {evidence.source_section && (
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                      Section: {formatLabel(evidence.source_section)}
                    </span>
                  )}
                </div>

                <p className="mt-3 text-sm text-slate-800">
                  {evidence.evidence_text || "No evidence text available."}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  Observed {formatDate(evidence.observed_at)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

export default function EvidencePage() {
  const router = useRouter();

  const [skillsData, setSkillsData] = useState<MySkillsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [resumeTitle, setResumeTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadResult, setUploadResult] =
    useState<ResumeUploadResponse | null>(null);

  const loadSkills = useCallback(async () => {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    try {
      setPageError("");

      const result = await getMySkills(accessToken);
      setSkillsData(result);
    } catch (error) {
      setPageError(
        error instanceof Error
          ? error.message
          : "Career evidence could not be loaded."
      );
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void loadSkills();
  }, [loadSkills]);

  const evidenceSourceCount = useMemo(() => {
    if (!skillsData) {
      return 0;
    }

    const sources = new Set<string>();

    skillsData.skills.forEach((skill) => {
      skill.evidence.forEach((evidence) => {
        sources.add(evidence.source_type);
      });
    });

    return sources.size;
  }, [skillsData]);

  async function handleUpload() {
    if (!selectedFile) {
      setUploadError("Choose a PDF resume first.");
      return;
    }

    if (
      selectedFile.type !== "application/pdf" &&
      !selectedFile.name.toLowerCase().endsWith(".pdf")
    ) {
      setUploadError("CareerPilot currently accepts PDF resumes.");
      return;
    }

    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    try {
      setUploading(true);
      setUploadError("");
      setUploadResult(null);

      const result = await uploadResume(
  accessToken,
  selectedFile,
  resumeTitle || "My Resume"
);

      setUploadResult(result);
      setSelectedFile(null);
      setResumeTitle("");

      await loadSkills();
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : "Resume upload failed."
      );
    } finally {
      setUploading(false);
    }
  }

  function handleLogout() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    router.replace("/login");
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
            <p className="text-sm font-semibold text-indigo-700">
              CareerPilot AI
            </p>
            <h1 className="mt-3 text-2xl font-semibold text-slate-950">
              Loading your career evidence...
            </h1>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-5">
          <div>
            <p className="text-lg font-bold text-slate-950">CareerPilot AI</p>
            <p className="text-sm text-slate-500">
              Evidence-Aware Career Intelligence
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Dashboard
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Log out
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10">
        <section>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-indigo-700">
            Career Evidence
          </p>

          <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Understand what CareerPilot knows about your skills.
          </h1>

          <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
            CareerPilot separates career claims, supporting evidence,
            evidence confidence and measured proficiency. A skill appearing on
            a resume is evidence, but it is not automatically treated as proof
            of proficiency.
          </p>
        </section>

        {pageError && (
          <section className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-5">
            <p className="font-semibold text-red-900">
              Career evidence could not be loaded
            </p>
            <p className="mt-2 text-sm text-red-800">{pageError}</p>

            <button
              type="button"
              onClick={() => {
                setLoading(true);
                void loadSkills();
              }}
              className="mt-4 rounded-xl bg-red-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Try again
            </button>
          </section>
        )}

        <section className="mt-10 grid gap-4 sm:grid-cols-3">
          <Metric
            label="Skills discovered"
            value={String(skillsData?.total_skills ?? 0)}
            description="Unique skills currently represented in your CareerPilot evidence profile."
          />

          <Metric
            label="Evidence records"
            value={String(skillsData?.total_evidence ?? 0)}
            description="Individual pieces of supporting evidence collected from your career data."
          />

          <Metric
            label="Evidence source types"
            value={String(evidenceSourceCount)}
            description="Different evidence-source families currently represented in this profile."
          />
        </section>

        <section className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
            <div>
              <p className="text-sm font-semibold text-indigo-700">
                Resume Evidence
              </p>

              <h2 className="mt-2 text-2xl font-semibold text-slate-950">
                Upload a resume
              </h2>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                CareerPilot parses the PDF and creates evidence records for
                recognized skills. Resume evidence represents information found
                in the document and does not independently verify proficiency.
              </p>
            </div>

            <div className="rounded-xl bg-slate-100 px-4 py-2 text-xs font-medium text-slate-600">
              PDF · maximum size enforced by backend
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr_auto]">
            <div>
              <label className="text-sm font-medium text-slate-700">
                Resume title
              </label>

              <input
                value={resumeTitle}
                onChange={(event) => setResumeTitle(event.target.value)}
                placeholder="Example: Software Engineering Resume"
                className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700">
                PDF resume
              </label>

              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(event) => {
                  setSelectedFile(event.target.files?.[0] ?? null);
                  setUploadError("");
                }}
                className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700"
              />
            </div>

            <div className="flex items-end">
              <button
                type="button"
                disabled={uploading}
                onClick={() => void handleUpload()}
                className="w-full rounded-xl bg-indigo-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-60 lg:w-auto"
              >
                {uploading ? "Processing..." : "Upload & analyze"}
              </button>
            </div>
          </div>

          {uploadError && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              {uploadError}
            </div>
          )}

          {uploadResult && (
            <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
              <p className="font-semibold text-emerald-950">
                Resume processing completed
              </p>

              <div className="mt-3 grid gap-2 text-sm text-emerald-900 sm:grid-cols-2 lg:grid-cols-4">
                <p>
                  <span className="font-medium">Title:</span>{" "}
                  {uploadResult.title}
                </p>

                <p>
                  <span className="font-medium">Version:</span>{" "}
                  {uploadResult.active_version_number}
                </p>

                <p>
                  <span className="font-medium">Status:</span>{" "}
                  {formatLabel(uploadResult.version.extraction_status)}
                </p>

                <p>
                  <span className="font-medium">Size:</span>{" "}
                  {formatBytes(uploadResult.version.file_size_bytes)}
                </p>
              </div>
            </div>
          )}
        </section>

        <section className="mt-10">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <p className="text-sm font-semibold text-indigo-700">
                Skill Evidence
              </p>

              <h2 className="mt-2 text-2xl font-semibold text-slate-950">
                Evidence-aware skill profile
              </h2>
            </div>

            <p className="text-sm text-slate-500">
              {skillsData?.total_skills ?? 0} skills ·{" "}
              {skillsData?.total_evidence ?? 0} evidence records
            </p>
          </div>

          {!skillsData || skillsData.skills.length === 0 ? (
            <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <h3 className="text-lg font-semibold text-slate-950">
                No skill evidence yet
              </h3>

              <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-600">
                Upload a resume to begin creating your CareerPilot evidence
                profile. Additional evidence sources such as projects and
                assessments can strengthen the Career Twin later.
              </p>
            </div>
          ) : (
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              {skillsData.skills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} />
              ))}
            </div>
          )}
        </section>

        <section className="mt-10 rounded-3xl border border-amber-200 bg-amber-50 p-6">
          <h2 className="font-semibold text-amber-950">
            How to interpret this page
          </h2>

          <p className="mt-2 text-sm leading-6 text-amber-900">
            Evidence confidence describes how strongly CareerPilot&apos;s
            available evidence supports a skill representation. Estimated
            proficiency is shown only when an appropriate measurement exists.
            Missing evidence does not mean that you lack a skill.
          </p>
        </section>

        <footer className="py-10 text-center text-xs leading-5 text-slate-500">
          CareerPilot AI · ACIF evidence model · Career evidence is decision
          support, not an employment or placement prediction.
        </footer>
      </div>
    </main>
  );
}