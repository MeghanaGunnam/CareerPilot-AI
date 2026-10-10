"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError } from "@/lib/api/client";
import { getJDAnalysis } from "@/lib/api/jobs";
import { APPLICATION_STATUSES, deleteApplication, getApplication, listApplications, saveApplication, type ApplicationInput, type ApplicationList, type ApplicationRecord } from "@/lib/api/applications";

const TOKEN = "careerpilot_access_token";
const button = "rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 disabled:opacity-50";
const input = "mt-1 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm focus:outline-2 focus:outline-indigo-600";
const empty: ApplicationInput = { company: "", job_title: "", location: null, employment_type: null, job_url: null, jd_analysis_id: null, applied_date: null, status: "SAVED", notes: null };

export default function ApplicationsPage() {
  const [data, setData] = useState<ApplicationList | null>(null);
  const [form, setForm] = useState<ApplicationInput>(empty);
  const [editing, setEditing] = useState<string | undefined>();
  const [filter, setFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [notice, setNotice] = useState("");
  const [auth, setAuth] = useState(false);
  const mutation = useRef<AbortController | null>(null);
  const detail = useRef<AbortController | null>(null);
  const fail = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.status === 401) { setAuth(true); setData(null); return "Sign in again."; }
    if (error instanceof ApiError && error.status === 422) return "Check required fields, status, HTTP(S) URL, date and linked JD UUID.";
    return error instanceof Error ? error.message : "Request failed.";
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const token = sessionStorage.getItem(TOKEN);
      if (!token) { setAuth(true); return; }
      try {
        const result = await listApplications(token, offset, filter, controller.signal);
        if (!controller.signal.aborted) { setData(result); setError(""); }
      } catch (error) { if (!controller.signal.aborted) setError(fail(error)); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [offset, filter, revision, fail]);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("jd");
    const token = sessionStorage.getItem(TOKEN);
    if (!id || !token) return;
    const controller = new AbortController();
    detail.current = controller;
    getJDAnalysis(token, id, controller.signal).then((jd) => {
      if (!controller.signal.aborted) {
        setForm({ ...empty, company: jd.company ?? "", job_title: jd.title, job_url: jd.source_url, jd_analysis_id: jd.id });
        setNotice("Prefilled from your saved JD. Review and save to create an application.");
      }
    }).catch((error: unknown) => { if (!controller.signal.aborted) setFormError(fail(error)); });
    return () => controller.abort();
  }, [fail]);
  useEffect(() => () => { mutation.current?.abort(); detail.current?.abort(); }, []);

  function reload(next = offset) { setLoading(true); setOffset(next); setRevision((n) => n + 1); }
  function field<K extends keyof ApplicationInput>(key: K, value: ApplicationInput[K]) { detail.current?.abort(); setForm((old) => ({ ...old, [key]: value })); }
  function resetForm() { detail.current?.abort(); setEditing(undefined); setForm(empty); setFormError(""); }

  async function edit(item: ApplicationRecord) {
    detail.current?.abort();
    const controller = new AbortController(); detail.current = controller;
    const token = sessionStorage.getItem(TOKEN);
    if (!token) { setAuth(true); return; }
    setFormError(""); setNotice("Loading application…");
    try {
      const record = await getApplication(token, item.id, controller.signal);
      if (!controller.signal.aborted) {
        setEditing(record.id);
        const { id: _id, created_at: _created, updated_at: _updated, ...values } = record;
        void _id; void _created; void _updated;
        setForm(values); setNotice("Editing saved application. Status changes are recorded only when you save.");
      }
    } catch (error) { if (!controller.signal.aborted) { setFormError(fail(error)); setNotice(""); } }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (mutation.current) return;
    detail.current?.abort();
    const token = sessionStorage.getItem(TOKEN);
    if (!token) { setAuth(true); return; }
    const controller = new AbortController(); mutation.current = controller;
    setBusy(true); setFormError(""); setNotice("");
    try {
      await saveApplication(token, { ...form, company: form.company.trim(), job_title: form.job_title.trim() }, editing, controller.signal);
      if (!controller.signal.aborted) { resetForm(); setNotice("Application saved."); reload(0); }
    } catch (error) { if (!controller.signal.aborted) setFormError(`${fail(error)} Your input is retained. Refresh history before retrying an uncertain save.`); }
    finally { if (!controller.signal.aborted) setBusy(false); mutation.current = null; }
  }

  async function remove(item: ApplicationRecord) {
    if (mutation.current || !window.confirm(`Delete the application for ${item.job_title} at ${item.company}? This does not delete the JD.`)) return;
    const token = sessionStorage.getItem(TOKEN);
    if (!token) { setAuth(true); return; }
    detail.current?.abort();
    const controller = new AbortController(); mutation.current = controller;
    setBusy(true); setFormError(""); setNotice("");
    try {
      await deleteApplication(token, item.id, controller.signal);
      if (!controller.signal.aborted) { if (editing === item.id) resetForm(); setNotice("Application deleted; JD preserved."); reload(0); }
    } catch (error) { if (!controller.signal.aborted) setFormError(`${fail(error)} Refresh to check the current state before retrying.`); }
    finally { if (!controller.signal.aborted) setBusy(false); mutation.current = null; }
  }

  return <main className="min-h-screen bg-slate-50 text-slate-950"><div className="mx-auto max-w-6xl px-6 py-10">
    <nav className="mb-6 flex flex-wrap gap-3"><Link href="/dashboard" className={button}>Dashboard</Link><Link href="/job-match" className={button}>Job Match</Link></nav>
    <h1 className="text-3xl font-bold">Application tracker</h1><p className="mt-3 text-sm text-slate-600">Track your own reported application status. CareerPilot does not infer outcomes or submit applications for you.</p>
    {auth ? <p role="alert" className="mt-6"><Link href="/login" className={button}>Sign in to access applications</Link></p> : <>
      {notice && <p role="status" className="mt-5 rounded-xl bg-indigo-50 p-4 text-sm">{notice}</p>}
      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6"><h2 className="text-xl font-semibold">{editing ? "Edit application" : "New application"}</h2>
        <form onSubmit={save}><fieldset disabled={busy} className="mt-4 grid gap-4 sm:grid-cols-2">
          {([['company', 'Company *', 200], ['job_title', 'Role *', 200], ['location', 'Location (optional)', 200], ['employment_type', 'Employment type (optional)', 100], ['job_url', 'Job URL (reference only)', 2048], ['jd_analysis_id', 'Linked JD UUID (optional)', 36]] as const).map(([key, title, max]) => <label key={key} className="text-sm font-medium">{title}<input className={input} required={key === "company" || key === "job_title"} type={key === "job_url" ? "url" : "text"} maxLength={max} value={form[key] ?? ""} onChange={(e) => field(key, (key === "company" || key === "job_title") ? e.target.value : e.target.value || null)} /></label>)}
          <label className="text-sm font-medium">Status<select className={input} value={form.status} onChange={(e) => field("status", e.target.value as ApplicationInput["status"])}>{APPLICATION_STATUSES.map((s) => <option key={s}>{s}</option>)}</select></label>
          <label className="text-sm font-medium">Applied date (only if known)<input type="date" className={input} value={form.applied_date ?? ""} onChange={(e) => field("applied_date", e.target.value || null)} /></label>
          <label className="text-sm font-medium sm:col-span-2">Private notes<textarea rows={4} maxLength={10000} className={input} value={form.notes ?? ""} onChange={(e) => field("notes", e.target.value || null)} /></label>
          <div className="flex gap-3"><button type="submit" className={button}>{busy ? "Saving…" : "Save application"}</button><button type="button" className={button} onClick={resetForm}>Clear / cancel</button></div>
        </fieldset></form>{formError && <p role="alert" className="mt-4 text-sm text-red-800">{formError}</p>}
      </section>
      <section className="mt-8" aria-busy={loading}><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">My applications</h2><div className="flex gap-3"><label className="text-sm">Status filter<select aria-label="Filter by status" className={input} disabled={busy} value={filter} onChange={(e) => { setLoading(true); setFilter(e.target.value); setOffset(0); }}><option value="">All statuses</option>{APPLICATION_STATUSES.map((s) => <option key={s}>{s}</option>)}</select></label><button className={button} disabled={busy || loading} onClick={() => reload()}>Refresh</button></div></div>
        {loading ? <p role="status" className="mt-5">Loading applications…</p> : error ? <div role="alert" className="mt-5"><p className="text-red-800">{error}</p><button className={button} onClick={() => reload()}>Retry</button></div> : data && <>
          {!data.items.length && <p className="mt-5 text-sm text-slate-600">No applications on this page for the selected filter.</p>}
          <div className="mt-5 grid gap-4 sm:grid-cols-2">{data.items.map((item) => <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="break-words font-semibold">{item.job_title} · {item.company}</h3><p className="mt-2 text-sm">{item.status} · {item.location ?? "Location not supplied"}</p><p className="mt-2 text-sm">Applied: {item.applied_date ?? "Not recorded"}</p><p className="mt-2 text-xs text-slate-500">Updated {new Date(item.updated_at).toLocaleString()}</p>{item.jd_analysis_id && <Link href={`/job-match?analysis=${encodeURIComponent(item.jd_analysis_id)}`} className="mt-3 inline-block text-sm text-indigo-700 underline">Open linked JD</Link>}<div className="mt-4 flex gap-2"><button className={button} disabled={busy} onClick={() => void edit(item)}>Edit / update status</button><button className={button} disabled={busy} onClick={() => void remove(item)}>Delete</button></div></article>)}</div>
          <div className="mt-5 flex items-center gap-3"><button className={button} disabled={offset === 0 || busy} onClick={() => reload(Math.max(0, offset - 10))}>Previous</button><span className="text-sm">{data.total} applications · page {Math.floor(offset / 10) + 1}</span><button className={button} disabled={offset + data.limit >= data.total || busy} onClick={() => reload(offset + 10)}>Next</button></div>
        </>}
      </section>
    </>}
  </div></main>;
}
