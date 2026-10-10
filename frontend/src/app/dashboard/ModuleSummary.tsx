"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getDashboardSummary, type DashboardSummary } from "@/lib/api/dashboard";

const card = "rounded-2xl border border-slate-200 bg-white p-5 shadow-sm";
const link = "mt-4 inline-block text-sm font-semibold text-indigo-700 underline";

export default function ModuleSummary() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [auth, setAuth] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const token = sessionStorage.getItem("careerpilot_access_token");
      if (!token) { setAuth(true); return; }
      try {
        const result = await getDashboardSummary(token, controller.signal);
        if (!controller.signal.aborted) { setData(result); setError(""); }
      } catch (error) {
        if (!controller.signal.aborted) {
          if (error instanceof ApiError && error.status === 401) { setAuth(true); setData(null); }
          else setError("Module summaries are unavailable. Existing module pages remain accessible from navigation.");
        }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [revision]);
  return <section className="mt-8" aria-labelledby="module-summary-title" aria-busy={loading}>
    <h2 id="module-summary-title" className="text-xl font-bold text-slate-950">Continue your next step</h2>
    {auth ? <Link href="/login" className={link}>Sign in to view your summaries</Link> : loading ? <p role="status" className="mt-4 text-sm text-slate-600">Loading your current module summaries…</p> : error ? <div role="alert" className={`${card} mt-4`}><p className="text-sm">{error}</p><button className={link} onClick={() => { setLoading(true); setRevision((value) => value + 1); }}>Retry summaries</button></div> : data && <>
      {(data.resume_count === 0 || data.completed_assessment_attempts === 0) && <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 rounded-xl bg-indigo-50 p-4 text-sm text-indigo-950">{data.resume_count === 0 && <Link href="/resume" className="underline">Upload your resume to begin building evidence.</Link>}{data.completed_assessment_attempts === 0 && <Link href="/assessment" className="underline">Complete an assessment to add measured evidence.</Link>}</div>}
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article className={card}><h3 className="font-semibold">Learning roadmap</h3><p className="mt-2 text-sm text-slate-600">{data.roadmap_total ? `${data.roadmap_status_counts.COMPLETED ?? 0} of ${data.roadmap_total} persisted items marked completed across your goals.` : "No roadmap items recorded yet. Review your existing ACIF-guided learning plan."}</p><Link href="/roadmap" className={link}>Review learning actions</Link></article>
        <article className={card}><h3 className="font-semibold">Recommended certifications</h3>{data.certification_preview.length > 0 ? <ul className="mt-2 space-y-2 text-sm text-slate-600">{data.certification_preview.map((item) => <li key={item.name}>{item.name} · {item.provider}</li>)}</ul> : <p className="mt-2 text-sm text-slate-600">{data.certification_status === "UNAVAILABLE" ? "Recommendations need a mapped goal and recorded Career Twin." : "No matching curated recommendations for your current gaps."}</p>}<p className="mt-2 text-xs text-slate-500">Suggestions, not earned credentials.</p><Link href="/certifications" className={link}>Explore recommendations</Link></article>
        <article className={card}><h3 className="font-semibold">Recent job analysis</h3>{data.latest_jd ? <><p className="mt-2 break-words text-sm">{data.latest_jd.title}{data.latest_jd.company ? ` · ${data.latest_jd.company}` : ""}</p><p className="mt-2 text-sm text-slate-600">CareerPilot Evidence Alignment: {data.latest_alignment?.value != null ? `${data.latest_alignment.numerator} of ${data.latest_alignment.denominator} eligible technologies strongly evidenced` : "unavailable — insufficient eligible information"}.</p><p className="mt-2 text-xs text-slate-500">Current recorded Twin comparison; not a hiring probability.</p><Link href={`/job-match?analysis=${encodeURIComponent(data.latest_jd.id)}`} className={link}>Open saved JD and explanation</Link></> : <><p className="mt-2 text-sm text-slate-600">Analyze a job description to compare it with your Career Twin.</p><Link href="/job-match" className={link}>Analyze a JD</Link></>}</article>
        <article className={card}><h3 className="font-semibold">Application pipeline</h3>{data.application_total ? <ul className="mt-2 grid grid-cols-2 gap-2 text-sm text-slate-600">{Object.entries(data.application_status_counts).filter(([, count]) => count > 0).map(([status, count]) => <li key={status}>{status.toLowerCase()}: {count}</li>)}</ul> : <p className="mt-2 text-sm text-slate-600">Track applications after analyzing roles.</p>}<p className="mt-2 text-xs text-slate-500">Your recorded statuses, not inferred outcomes.</p><Link href="/applications" className={link}>Manage applications</Link></article>
        <article className={card}><h3 className="font-semibold">Career Twin progress</h3><p className="mt-2 text-sm text-slate-600">{data.progress.evidence_entry_change === null ? data.progress.message : `Recorded evidence-entry change: ${data.progress.evidence_entry_change > 0 ? "+" : ""}${data.progress.evidence_entry_change} between the latest two snapshots.`}</p><p className="mt-2 text-xs text-slate-500">No continuous history or proficiency growth inferred.</p><Link href="/progress" className={link}>View recorded progress</Link></article>
        <article className={card}><h3 className="font-semibold">CareerPilot AI Assistant</h3><p className="mt-2 text-sm text-slate-600">{data.assistant.provider_status === "READY" ? "Ask about bounded, grounded CareerPilot statements. Provider use requires your consent." : "CareerPilot AI Assistant is not configured yet."}</p><p className="mt-2 text-xs text-slate-500">Structured grounding, not semantic RAG.</p><Link href="/assistant" className={link}>Open assistant</Link></article>
      </div>
    </>}
  </section>;
}
