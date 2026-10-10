"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { hasAssessmentEvidence } from "@/lib/evidence-display";

import {
  getMySkills,
  MySkillsResponse,
  SkillEvidence,
  StudentSkill,
} from "@/lib/api/skills";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";

function formatLabel(value: string | null | undefined) {
  if (!value) return "Unknown";

  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string | null) {
  if (!value) return "Not verified";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Not verified";
  }

  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatScore(value: number | null) {
  if (value === null) return "Not calculated";

  return `${Math.round(value * 100)}%`;
}

function EvidenceBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase();

  const style =
    normalized === "VERIFIED"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : normalized === "ASSESSED"
        ? "bg-blue-50 text-blue-700 border-blue-200"
        : normalized === "CLAIMED"
          ? "bg-amber-50 text-amber-700 border-amber-200"
          : "bg-slate-50 text-slate-700 border-slate-200";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${style}`}
    >
      {formatLabel(status)}
    </span>
  );
}

function EvidenceItem({ evidence }: { evidence: SkillEvidence }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <EvidenceBadge status={evidence.evidence_status} />

        <span className="text-xs font-medium text-slate-500">
          {formatLabel(evidence.source_type)}
        </span>

        {evidence.source_section && (
          <>
            <span className="text-xs text-slate-300">•</span>
            <span className="text-xs text-slate-500">
              {formatLabel(evidence.source_section)}
            </span>
          </>
        )}
      </div>

      {evidence.evidence_text && (
        <p className="mt-3 text-sm text-slate-700">
          Evidence:{" "}
          <span className="font-medium">
            {evidence.evidence_text}
          </span>
        </p>
      )}

      <p className="mt-2 text-xs text-slate-400">
        Observed {formatDate(evidence.observed_at)}
      </p>
    </div>
  );
}

function SkillCard({ skill }: { skill: StudentSkill }) {
  const [expanded, setExpanded] = useState(false);

  const hasAssessment = hasAssessmentEvidence(skill.evidence);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              {skill.canonical_name}
            </h2>

            {skill.category && (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                {skill.category}
              </span>
            )}
          </div>

          <p className="mt-1 text-sm text-slate-500">
            {skill.evidence.length} evidence{" "}
            {skill.evidence.length === 1 ? "record" : "records"}
          </p>
        </div>

        <span
          className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${
            hasAssessment
              ? "bg-emerald-50 text-emerald-700"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          {hasAssessment
            ? "Measured evidence available"
            : "Evidence available · proficiency not assessed"}
        </span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Assessment-derived estimate
          </p>
          <p className="mt-1 font-semibold text-slate-800">
            {!hasAssessment || skill.estimated_proficiency === null
              ? "Not assessed"
              : formatScore(skill.estimated_proficiency)}
          </p>
          <p className="mt-1 text-xs text-slate-500">Assessment-specific; not universal proficiency.</p>
        </div>

        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Evidence confidence
          </p>
          <p className="mt-1 font-semibold text-slate-800">
            {formatScore(skill.evidence_confidence)}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Last verified
          </p>
          <p className="mt-1 font-semibold text-slate-800">
            {formatDate(skill.last_verified_at)}
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="mt-5 text-sm font-semibold text-slate-700 transition hover:text-slate-950"
      >
        {expanded ? "Hide evidence" : "View evidence"}
        <span className="ml-1">{expanded ? "↑" : "↓"}</span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-3">
          {skill.evidence.map((evidence) => (
            <EvidenceItem
              key={evidence.id}
              evidence={evidence}
            />
          ))}
        </div>
      )}
    </article>
  );
}

export default function SkillsPage() {
  const router = useRouter();

  const [data, setData] = useState<MySkillsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function loadSkills() {
      const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

      if (!accessToken) {
        router.replace("/login");
        return;
      }

      try {
        const response = await getMySkills(accessToken);
        setData(response);
      } catch (err) {
        console.error("Failed to load skills:", err);

        setError(
          "We could not load your skill evidence. Your session may have expired."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadSkills();
  }, [router]);

  const filteredSkills = useMemo(() => {
    if (!data) return [];

    const query = search.trim().toLowerCase();

    if (!query) {
      return data.skills;
    }

    return data.skills.filter((skill) =>
      skill.canonical_name.toLowerCase().includes(query)
    );
  }, [data, search]);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="text-sm font-medium text-slate-500">
            Loading your skill evidence...
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-3xl px-6 py-16">
          <div className="rounded-2xl border border-red-200 bg-white p-6">
            <h1 className="text-xl font-bold text-slate-900">
              Skills & Evidence
            </h1>

            <p className="mt-3 text-sm text-red-600">
              {error}
            </p>

            <button
              type="button"
              onClick={() => router.push("/login")}
              className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            >
              Sign in again
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
          <div>
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="mb-4 text-sm font-semibold text-slate-500 hover:text-slate-900"
            >
              ← Back to dashboard
            </button>

            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
              CareerPilot AI
            </p>

            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
              Skills & Evidence
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
              Review the skills CareerPilot has identified and the evidence
              supporting them. Resume mentions are evidence signals; they do
              not automatically represent verified proficiency.
            </p>
          </div>
        </div>

        <section className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">
              Identified skills
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-950">
              {data.total_skills}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">
              Evidence records
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-950">
              {data.total_evidence}
            </p>
          </div>
        </section>

        <section className="mt-8 rounded-2xl border border-blue-100 bg-blue-50 p-5">
          <h2 className="font-semibold text-slate-900">
            How CareerPilot interprets evidence
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            A skill appearing in a resume can establish that supporting
            evidence exists. CareerPilot keeps this separate from measured
            proficiency, evidence confidence, and verified competency so that
            unsupported scores are not invented.
          </p>
        </section>

        {data.skills.length === 0 ? (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <h2 className="text-lg font-bold text-slate-900">
              No skill evidence yet
            </h2>

            <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
              Uploading a resume or completing supported assessments can add
              evidence to your Career Twin.
            </p>
          </section>
        ) : (
          <>
            <section className="mt-8">
              <label
                htmlFor="skill-search"
                className="text-sm font-semibold text-slate-700"
              >
                Search skills
              </label>

              <input
                id="skill-search"
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search Python, Java, SQL..."
                className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500"
              />
            </section>

            <section className="mt-6 space-y-4">
              {filteredSkills.length > 0 ? (
                filteredSkills.map((skill) => (
                  <SkillCard
                    key={skill.id}
                    skill={skill}
                  />
                ))
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
                  <p className="text-sm text-slate-500">
                    No skills match &quot;{search}&quot;.
                  </p>
                </div>
              )}
            </section>
          </>
        )}

        <footer className="mt-10 border-t border-slate-200 pt-6">
          <p className="text-xs leading-5 text-slate-500">
            CareerPilot distinguishes observed evidence from measured
            proficiency. Evidence shown here should not be interpreted as a
            hiring, placement, employability, or career-success probability.
          </p>
        </footer>
      </div>
    </main>
  );
}
