"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getMySkills,
  MySkillsResponse,
  SkillEvidence,
  StudentSkill,
} from "@/lib/api/skills";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";

function formatSource(source: string) {
  switch (source.toUpperCase()) {
    case "RESUME":
      return "Resume";
    case "ASSESSMENT":
      return "Assessment";
    case "PROJECT":
      return "Project";
    case "CERTIFICATION":
      return "Certification";
    default:
      return source
        .toLowerCase()
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
  }
}

function formatStatus(status: string) {
  return status
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function getSourceClasses(source: string) {
  switch (source.toUpperCase()) {
    case "ASSESSMENT":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "RESUME":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "PROJECT":
      return "bg-violet-50 text-violet-700 border-violet-200";
    case "CERTIFICATION":
      return "bg-amber-50 text-amber-700 border-amber-200";
    default:
      return "bg-slate-50 text-slate-700 border-slate-200";
  }
}

function EvidenceItem({ evidence }: { evidence: SkillEvidence }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${getSourceClasses(
            evidence.source_type
          )}`}
        >
          {formatSource(evidence.source_type)}
        </span>

        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {formatStatus(evidence.evidence_status)}
        </span>

        {evidence.source_section && (
          <span className="text-xs text-slate-500">
            {evidence.source_section}
          </span>
        )}
      </div>

      {evidence.evidence_text && (
        <p className="mt-3 text-sm font-medium text-slate-800">
          {evidence.evidence_text}
        </p>
      )}

      {evidence.evidence_strength !== null && (
        <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2">
          <p className="text-xs text-slate-500">
            Assessment evidence strength
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-800">
            {(evidence.evidence_strength * 100).toFixed(0)}%
          </p>
        </div>
      )}

      <p className="mt-3 text-xs text-slate-400">
        Observed {formatDate(evidence.observed_at)}
      </p>
    </div>
  );
}

function SkillCard({ skill }: { skill: StudentSkill }) {
  const [expanded, setExpanded] = useState(false);

  const sourceCount = new Set(
    skill.evidence.map((item) => item.source_type)
  ).size;

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="w-full p-5 text-left transition hover:bg-slate-50"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {skill.canonical_name}
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              {skill.evidence.length} evidence{" "}
              {skill.evidence.length === 1 ? "record" : "records"} from{" "}
              {sourceCount} {sourceCount === 1 ? "source" : "sources"}
            </p>
          </div>

          <span className="text-xl text-slate-400">
            {expanded ? "−" : "+"}
          </span>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {Array.from(
            new Set(skill.evidence.map((item) => item.source_type))
          ).map((source) => (
            <span
              key={source}
              className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${getSourceClasses(
                source
              )}`}
            >
              {formatSource(source)}
            </span>
          ))}
        </div>

        {skill.estimated_proficiency !== null && (
          <p className="mt-4 text-xs text-slate-500">
            Measured proficiency is available for this skill.
          </p>
        )}
      </button>

      {expanded && (
        <div className="border-t border-slate-200 bg-slate-50 p-5">
          <div className="mb-4">
            <h3 className="font-semibold text-slate-900">
              Evidence provenance
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              These records show why CareerPilot knows about this skill.
              Evidence does not automatically prove proficiency.
            </p>
          </div>

          <div className="space-y-3">
            {skill.evidence.map((evidence) => (
              <EvidenceItem
                key={evidence.id}
                evidence={evidence}
              />
            ))}
          </div>
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
        setLoading(true);
        setError("");

        const response = await getMySkills(accessToken);
        setData(response);
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Skills and evidence could not be loaded."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadSkills();
  }, [router]);

  const filteredSkills = useMemo(() => {
    if (!data) {
      return [];
    }

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
      <main className="min-h-screen bg-slate-50 px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <p className="text-sm font-semibold text-blue-600">
            CareerPilot AI
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Loading skills and evidence...
          </h1>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50 px-6 py-16">
        <div className="mx-auto max-w-3xl rounded-2xl border border-red-200 bg-white p-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-red-600">
            Skills error
          </p>

          <h1 className="mt-2 text-2xl font-bold text-slate-900">
            Skills and evidence could not be loaded
          </h1>

          <p className="mt-3 text-sm text-slate-600">
            {error}
          </p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-6 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white"
          >
            Try Again
          </button>
        </div>
      </main>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-lg font-bold text-slate-900">
              CareerPilot AI
            </p>
            <p className="text-xs text-slate-500">
              Evidence-Aware Career Intelligence
            </p>
          </div>

          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-10">
        <section>
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Evidence-Aware Career Twin
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            Skills & Evidence
          </h1>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Review the skills CareerPilot has discovered and the evidence
            supporting each one. Resume mentions are treated as evidence
            claims, while assessment results are stored separately as
            measured evidence.
          </p>
        </section>

        <section className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">
              Skills discovered
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {data.total_skills}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">
              Evidence records
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-900">
              {data.total_evidence}
            </p>
          </div>
        </section>

        <section className="mt-8">
          <label
            htmlFor="skill-search"
            className="text-sm font-semibold text-slate-700"
          >
            Search skills
          </label>

          <input
            id="skill-search"
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search Python, Java, SQL..."
            className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </section>

        <section className="mt-8">
          <div className="mb-4 flex items-end justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Evidence inventory
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {filteredSkills.length} skills shown
              </p>
            </div>
          </div>

          {filteredSkills.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <p className="font-semibold text-slate-800">
                No matching skill found
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Try another search term.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {filteredSkills.map((skill) => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                />
              ))}
            </div>
          )}
        </section>

        <section className="mt-10 rounded-2xl border border-blue-100 bg-blue-50 p-5">
          <h2 className="font-semibold text-slate-900">
            How to interpret this page
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            A skill appearing here means CareerPilot has evidence associated
            with it. Resume mentions, project detections, certifications and
            assessments have different evidential meaning. A detected or
            claimed skill should not be interpreted as verified proficiency.
          </p>
        </section>
      </div>
    </main>
  );
}