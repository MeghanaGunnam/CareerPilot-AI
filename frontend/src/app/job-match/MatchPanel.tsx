"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getJDMatch, type JDMatch } from "@/lib/api/jobs";

const button = "rounded-xl border border-indigo-300 px-4 py-2 text-sm font-semibold text-indigo-800 hover:bg-indigo-50 disabled:opacity-50";
const label = (value: string) => value.replaceAll("_", " ").toLowerCase();

export default function MatchPanel({ analysisId }: { analysisId: string }) {
  const [result, setResult] = useState<JDMatch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [auth, setAuth] = useState(false);
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);

  async function compare() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const token = sessionStorage.getItem("careerpilot_access_token");
    if (!token) { setResult(null); setAuth(true); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await getJDMatch(token, analysisId, controller.signal);
      if (!controller.signal.aborted) setResult(data);
    } catch (err) {
      if (!controller.signal.aborted) {
        if (err instanceof ApiError && err.status === 401) setAuth(true);
        else setError(err instanceof Error ? err.message : "Comparison failed.");
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  return <section className="mt-8 rounded-3xl border border-indigo-200 bg-white p-6" aria-labelledby="match-title">
    <h2 id="match-title" className="text-xl font-bold">Compare with my Career Twin</h2>
    <p className="mt-2 text-sm leading-6 text-slate-600">Read-only comparison against your latest recorded snapshot. Missing evidence is not missing skill. This does not estimate hiring or placement probability.</p>
    {auth ? <p role="alert" className="mt-4"><Link href="/login" className={button}>Sign in to compare</Link></p> : <button type="button" disabled={loading} onClick={() => void compare()} className={`${button} mt-4`}>{loading ? "Comparing…" : result ? "Refresh comparison" : "Compare with my Career Twin"}</button>}
    {loading && <p role="status" className="mt-3 text-sm">Loading recorded evidence…</p>}
    {error && <p role="alert" className="mt-4 text-sm text-red-800">{error} Use the compare button to retry.</p>}
    {result && <>
      {result.status === "UNAVAILABLE" && <p role="status" className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-950">{result.unavailable_reason} No missing-skill inference has been made.</p>}
      <div className="mt-5 rounded-xl bg-slate-50 p-5">
        <h3 className="font-semibold">{result.alignment.label}</h3>
        <p className="mt-2 text-xl font-bold">{result.alignment.value === null ? "Unavailable — insufficient eligible information" : `${result.alignment.numerator} of ${result.alignment.denominator} eligible technologies have strong evidence`}</p>
        <p className="mt-3 text-sm leading-6 text-slate-600">{result.alignment.methodology}</p>
        {result.alignment.eligible_technologies.length > 0 && <p className="mt-2 text-sm">Eligible: {result.alignment.eligible_technologies.join(", ")}</p>}
      </div>
      <p className="mt-3 text-xs text-slate-500">Snapshot {result.snapshot_version ?? "unavailable"}{result.snapshot_created_at ? ` · recorded ${new Date(result.snapshot_created_at).toLocaleString()}` : ""} · {result.model_version} · {result.matching_version}</p>
      <p className="mt-2 text-sm text-slate-600">{result.interpretation}</p>
      {result.requirements.length === 0 && <p className="mt-5 text-sm">No persisted requirement records are available to compare.</p>}
      <div className="mt-5 space-y-4">{result.requirements.map((row) => <article key={row.requirement.id} className="rounded-2xl border border-slate-200 p-4">
        <h3 className="font-semibold">{row.canonical_technology ?? "Unmapped requirement"} · {label(row.state)}</h3>
        <blockquote className="mt-3 whitespace-pre-wrap break-words border-l-2 border-indigo-200 pl-3 text-sm leading-6">{row.requirement.quote}</blockquote>
        <p className="mt-2 text-xs text-slate-500">FACT_FROM_JD: quote only · characters {row.requirement.source_start}–{row.requirement.source_end} · inferred group: {row.requirement.group}</p>
        <p className="mt-3 text-sm">{row.explanation}</p>
        <p className="mt-2 text-sm text-slate-600">Strength interpretation: {label(row.strength)}. {row.strength_explanation}</p>
        <p className="mt-2 text-sm text-slate-600">{row.included_in_alignment ? "Included in alignment (deduplicated by technology)." : `Excluded: ${row.exclusion_reason}`}</p>
        <p className="mt-3 text-sm">Evidence records: {row.evidence.evidence_count} · Sources: {row.evidence.source_types.join(", ") || "none recorded"}</p>
        <p className="mt-1 text-sm">ACIF evidence confidence: {row.evidence.evidence_confidence === null ? "unavailable" : row.evidence.evidence_confidence.toFixed(2)} · Measurement: {label(row.evidence.measurement_status)}{row.evidence.assessment_measurement !== null ? ` (${row.evidence.assessment_measurement.toFixed(2)}, assessment-specific only)` : ""}</p>
        {row.actions.length > 0 && <ul className="mt-3 space-y-2">{row.actions.map((action, index) => <li key={`${action.provenance}-${index}`} className="text-sm"><Link href={action.href} className="text-indigo-700 underline">{action.label}</Link></li>)}</ul>}
      </article>)}</div>
      <Link href="/roadmap" className={`${button} mt-5 inline-block`}>Review my existing learning roadmap</Link>
    </>}
  </section>;
}
