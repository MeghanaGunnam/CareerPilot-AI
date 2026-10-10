"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { ApiError } from "@/lib/api/client";
import {
  getCertificationRecommendations,
  type CertificationRecommendation,
  type CertificationRecommendationsResponse,
} from "@/lib/api/certification-recommendations";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";
const PROVIDER_HOSTS: Record<string, string> = {
  "Python Institute": "pythoninstitute.org",
  Oracle: "education.oracle.com",
  "The Linux Foundation": "training.linuxfoundation.org",
  Microsoft: "learn.microsoft.com",
  "Amazon Web Services": "aws.amazon.com",
};
const LINK_CLASSES = "rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600";

// Only use the catalog's supplied URL, on the exact official provider host.
function providerUrl(item: CertificationRecommendation): string | null {
  try {
    const url = new URL(item.official_url);
    if (
      url.protocol === "https:" &&
      url.hostname === PROVIDER_HOSTS[item.provider] &&
      !url.username && !url.password && !url.port &&
      item.provenance.source === "CURATED_OFFICIAL_PROVIDER_CATALOG" &&
      item.provenance.source_url === item.official_url
    ) return url.href;
  } catch {
    // Invalid or unsupported provider URLs are displayed without a link.
  }
  return null;
}

function RecommendationCard({ item }: { item: CertificationRecommendation }) {
  const url = providerUrl(item);
  const blocked = item.provenance.verification_status === "FETCH_BLOCKED_HTTP_403";

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{item.provider} · {item.category}</p>
          <h2 className="mt-2 text-xl font-bold text-slate-950">{item.name}</h2>
        </div>
        <span className="w-fit shrink-0 rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-700">Rank {item.priority}</span>
      </div>

      <h3 className="mt-5 text-sm font-semibold text-slate-900">Why this is recommended</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{item.reason}</p>
      <div className="mt-4 flex flex-wrap gap-2" aria-label="Relevant skills">
        {item.relevant_skills.map((skill) => <span key={skill} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">{skill}</span>)}
      </div>

      {item.gaps.length > 0 && (
        <div className="mt-5 rounded-xl bg-slate-50 p-4">
          <h3 className="text-sm font-semibold text-slate-900">Current evidence gaps</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-600">
            {item.gaps.map((gap) => (
              <li key={gap.skill}><span className="font-medium">{gap.skill}:</span> {gap.state === "MISSING_EVIDENCE" ? "Missing evidence" : "Evidence needs strengthening"}</li>
            ))}
          </ul>
        </div>
      )}

      <div className={`mt-5 rounded-xl border p-4 text-sm ${blocked ? "border-amber-200 bg-amber-50 text-amber-900" : "border-slate-200 bg-slate-50 text-slate-700"}`}>
        <p className="font-semibold">{blocked ? "Limited source verification — fetch blocked (HTTP 403)" : "Official page retrieved — identity and topic only"}</p>
        <p className="mt-2 leading-6">{item.provenance.verification_note}</p>
        <p className="mt-2 text-xs">URL check attempted: {item.provenance.url_checked_on}</p>
      </div>
      <details className="mt-4 text-sm text-slate-600">
        <summary className="cursor-pointer font-semibold text-slate-700">Source and coverage limitations</summary>
        <div className="mt-3 space-y-2 break-words leading-6">
          <p>Source: {item.provenance.source.replaceAll("_", " ")}</p>
          <p>Catalog: {item.provenance.catalog_version}</p>
          <p>{item.provenance.coverage_basis}</p>
          <p>{item.provenance.limitations}</p>
        </div>
      </details>
      <div className="mt-5">
        {url ? (
          <a href={url} target="_blank" rel="noopener noreferrer" className="inline-block rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">Visit official provider <span className="sr-only">for {item.name}</span> (opens new tab)</a>
        ) : <p className="text-sm text-slate-500">Official provider link unavailable.</p>}
      </div>
    </article>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "auth" }
  | { status: "error"; message: string }
  | { status: "ready"; data: CertificationRecommendationsResponse };

export default function CertificationsPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    async function load() {
      try {
        const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
        if (!accessToken) {
          if (active) setState({ status: "auth" });
          return;
        }
        const data = await getCertificationRecommendations(accessToken, controller.signal);
        if (active) setState({ status: "ready", data });
      } catch (error) {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          setState({ status: "auth" });
        } else {
          setState({ status: "error", message: error instanceof Error ? error.message : "Recommendations could not be loaded." });
        }
      }
    }

    void load();
    return () => {
      active = false;
      controller.abort();
    };
  }, [attempt]);

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <header>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">CareerPilot AI</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Recommended Certifications</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">Explore curated certification options related to your target role and current evidence gaps. Rank is recommendation order, not a hiring score. These suggestions do not establish proficiency or guarantee employment.</p>
          <nav aria-label="Certification navigation" className="mt-5 flex flex-wrap gap-3">
            <Link href="/dashboard" className={LINK_CLASSES}>Back to dashboard</Link>
            <Link href="/profile" className={LINK_CLASSES}>Manage earned certifications in your profile</Link>
          </nav>
        </header>

        <div className="mt-8" aria-live="polite" aria-busy={state.status === "loading"}>
          {state.status === "loading" && <p role="status" className="text-sm text-slate-600">Loading recommended certifications…</p>}
          {state.status === "auth" && (
            <section className="rounded-2xl border border-slate-200 bg-white p-6">
              <h2 className="text-lg font-semibold text-slate-950">Sign in required</h2>
              <p className="mt-2 text-sm text-slate-600">Your session may have expired. Sign in to view your recommendations.</p>
              <Link href="/login" className={`mt-4 inline-block ${LINK_CLASSES}`}>Sign in</Link>
            </section>
          )}
          {state.status === "error" && (
            <section role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-6">
              <h2 className="text-lg font-semibold text-red-900">Recommendations could not be loaded</h2>
              <p className="mt-2 text-sm text-red-800">{state.message}</p>
              <button type="button" className={`mt-4 ${LINK_CLASSES}`} onClick={() => { setState({ status: "loading" }); setAttempt((value) => value + 1); }}>Try again</button>
            </section>
          )}
          {state.status === "ready" && (
            <>
              <section className="rounded-2xl border border-slate-200 bg-white p-6">
                <h2 className="text-xl font-bold text-slate-950">{state.data.target_role}</h2>
                <p className="mt-2 text-sm text-slate-600">O*NET occupational anchor: {state.data.occupational_anchor.title} · {state.data.occupational_anchor.onet_soc_code}</p>
                <p className="mt-4 text-sm leading-6 text-slate-600">{state.data.interpretation}</p>
                <p className="mt-3 text-sm leading-6 text-slate-600">Methodology: {state.data.methodology}</p>
                <p className="mt-3 text-xs text-slate-500">Model {state.data.model_version} · Career Twin snapshot v{state.data.snapshot_version}</p>
              </section>
              {state.data.recommendations.length === 0 ? (
                <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
                  <h2 className="text-lg font-semibold text-slate-950">No recommendations in the current catalog</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">No catalog entries matched your current recommendation criteria. This does not mean your evidence is complete or that no relevant certifications exist.</p>
                </section>
              ) : (
                <div className="mt-6 space-y-6">
                  {state.data.recommendations.map((item) => <RecommendationCard key={item.key} item={item} />)}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
}
