"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { getProgress, type CareerProgress } from "@/lib/api/progress";

const button = "rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 disabled:opacity-50";
const label = (value: string) => value.replaceAll("_", " ").toLowerCase();
const count = (value: number | null) => value === null ? "Not recorded / unavailable" : String(value);

export default function ProgressPage() {
  const [data, setData] = useState<CareerProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [auth, setAuth] = useState(false);
  const [offset, setOffset] = useState(0);
  const [eventOffset, setEventOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const token = sessionStorage.getItem("careerpilot_access_token");
      if (!token) { setAuth(true); return; }
      try {
        const result = await getProgress(token, offset, eventOffset, controller.signal);
        if (!controller.signal.aborted) { setData(result); setError(""); }
      } catch (error) {
        if (!controller.signal.aborted) {
          if (error instanceof ApiError && error.status === 401) { setAuth(true); setData(null); }
          else setError(error instanceof Error ? error.message : "Progress could not be loaded.");
        }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [offset, eventOffset, revision]);
  function reload() { setLoading(true); setRevision((n) => n + 1); }
  function page(next: number, events = false) { setLoading(true); if (events) setEventOffset(next); else setOffset(next); }

  return <main className="min-h-screen bg-slate-50 text-slate-950"><div className="mx-auto max-w-6xl px-6 py-10">
    <nav className="mb-6 flex flex-wrap gap-3"><Link href="/dashboard" className={button}>Dashboard</Link><Link href="/roadmap" className={button}>Learning roadmap</Link><Link href="/assessment" className={button}>Assessments</Link></nav>
    <div className="flex items-start justify-between gap-4"><div><h1 className="text-3xl font-bold">Career Twin progress</h1><p className="mt-3 text-sm text-slate-600">Recorded snapshots and events—not a reconstructed history or continuous tracking.</p></div><button className={button} disabled={loading || auth} onClick={reload}>Refresh</button></div>
    {auth ? <p role="alert" className="mt-6"><Link className={button} href="/login">Sign in to view progress</Link></p> : loading ? <p role="status" className="mt-8">Loading recorded history…</p> : error ? <div role="alert" className="mt-6"><p className="text-red-800">{error}</p><button className={`${button} mt-3`} onClick={reload}>Retry</button></div> : data && <>
      <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">Latest recorded change</h2><p className="mt-3 text-sm">{data.history_message}</p>
        <p className="mt-2 text-xs text-slate-500">Current recorded snapshot: {data.current_snapshot ? `v${data.current_snapshot.version} · ${new Date(data.current_snapshot.created_at).toLocaleString()}` : "None"} · Previous: {data.previous_snapshot ? `v${data.previous_snapshot.version} · ${new Date(data.previous_snapshot.created_at).toLocaleString()}` : "None"}</p>
        <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Counts stored in the latest two snapshots</caption><thead><tr className="border-b"><th className="p-3">Recorded metric</th><th className="p-3">Previous recorded value</th><th className="p-3">Current recorded value</th><th className="p-3">Change</th></tr></thead><tbody>{data.comparison.map((row) => <tr key={row.key} className="border-b border-slate-100"><th scope="row" className="p-3 font-medium">{row.label}</th><td className="p-3">{count(row.previous_recorded_value)}</td><td className="p-3">{count(row.current_recorded_value)}</td><td className="p-3">{row.change === null ? "Not enough comparable history" : `${row.change > 0 ? "+" : ""}${row.change}`}</td></tr>)}</tbody></table></div>
        <p className="mt-4 rounded-xl bg-indigo-50 p-4 text-sm leading-6 text-indigo-950">{data.interpretation}</p>
      </section>
      <section className="mt-6 grid gap-4 sm:grid-cols-2"><article className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Current recorded roadmap status</h2><p className="mt-2 text-sm text-slate-600">{data.roadmap_total} persisted items across your goals. Completion is not inferred from evidence.</p><ul className="mt-4 space-y-2">{Object.entries(data.roadmap_status_counts).map(([status, value]) => <li key={status} className="flex justify-between text-sm"><span>{label(status)}</span><span>{value}</span></li>)}</ul></article><article className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Current assessment activity</h2><p className="mt-3 text-2xl font-bold">{data.completed_assessment_attempts}</p><p className="mt-2 text-sm text-slate-600">Attempts explicitly marked completed with a recorded completion timestamp. This current total is not a historical proficiency score.</p></article></section>
      <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">Career Twin snapshot history</h2><p className="mt-2 text-sm text-slate-500">Newest recorded version first · {data.snapshot_total} snapshots</p>
        {data.snapshots.length === 0 ? <p className="mt-4 text-sm">No snapshots on this page. Not enough history yet.</p> : <ol className="mt-5 space-y-3">{data.snapshots.map((snapshot) => <li key={snapshot.id} className="rounded-xl bg-slate-50 p-4"><h3 className="font-semibold">Version {snapshot.version} · {label(snapshot.trigger_type)}</h3><p className="mt-1 text-xs text-slate-500">{new Date(snapshot.created_at).toLocaleString()} · schema {snapshot.schema_version}</p><p className="mt-2 text-sm">Skills: {count(snapshot.counts.skill_records)} · Evidence entries: {count(snapshot.counts.evidence_entries)} · Assessment evidence entries: {count(snapshot.counts.assessment_evidence_entries)}</p></li>)}</ol>}
        <div className="mt-4 flex gap-3"><button className={button} disabled={offset === 0} onClick={() => page(Math.max(0, offset - 20))}>Newer snapshots</button><button className={button} disabled={offset + data.limit >= data.snapshot_total} onClick={() => page(offset + 20)}>Older snapshots</button></div>
      </section>
      <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">Recorded event timeline</h2><p className="mt-2 text-sm text-slate-500">Newest event first · {data.event_total} recorded events</p>
        {data.events.length === 0 ? <p className="mt-4 text-sm">No recorded events on this page.</p> : <ol className="mt-5 space-y-3">{data.events.map((event) => <li key={event.id} className="border-l-2 border-indigo-200 pl-4"><p className="text-sm font-semibold">{label(event.event_type)}</p><p className="mt-1 text-xs text-slate-600">{new Date(event.occurred_at).toLocaleString()} · source: {event.source_type}{event.snapshot_version !== null ? ` · recorded snapshot reference v${event.snapshot_version}` : ""}</p></li>)}</ol>}
        <div className="mt-4 flex gap-3"><button className={button} disabled={eventOffset === 0} onClick={() => page(Math.max(0, eventOffset - 20), true)}>Newer events</button><button className={button} disabled={eventOffset + data.limit >= data.event_total} onClick={() => page(eventOffset + 20, true)}>Older events</button></div>
      </section>
    </>}
  </div></main>;
}
