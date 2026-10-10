"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError } from "@/lib/api/client";
import { createJDAnalysis, getJDAnalysis, listJDAnalyses, type JDAnalysis, type JDAnalysisList } from "@/lib/api/jobs";
import MatchPanel from "./MatchPanel";

const TOKEN_KEY = "careerpilot_access_token";
const PAGE_SIZE = 10;
const buttonClass = "rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600";
const inputClass = "mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 focus:outline-2 focus:outline-indigo-600";

function errorMessage(error: unknown) {
  if (error instanceof ApiError && error.status === 422) {
    return "Check the title, company, HTTP(S) source URL, and pasted description. The server could not validate this input.";
  }
  return error instanceof Error ? error.message : "The request failed. Please try again.";
}

function AnalysisDetail({ analysis }: { analysis: JDAnalysis }) {
  return (
    <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" aria-labelledby="analysis-title">
      <p className="text-sm font-semibold text-indigo-700">Saved extraction</p>
      <h2 id="analysis-title" className="mt-2 break-words text-2xl font-bold">{analysis.title}</h2>
      {analysis.company && <p className="mt-2 break-words text-slate-600">{analysis.company}</p>}
      <p className="mt-2 text-xs text-slate-500">Saved {new Date(analysis.created_at).toLocaleString()} · Extractor {analysis.extractor_version}</p>
      <Link href={`/applications?jd=${encodeURIComponent(analysis.id)}`} className={`${buttonClass} mt-4 inline-block`}>Track this application</Link>
      <Link href={`/assistant?jd=${encodeURIComponent(analysis.id)}`} className={`${buttonClass} mt-4 ml-2 inline-block`}>Ask about this saved JD</Link>
      {analysis.source_url && <p className="mt-2 break-all text-sm text-slate-600">Source URL (reference only): {analysis.source_url}</p>}
      <div className="mt-5 rounded-xl border border-indigo-100 bg-indigo-50 p-4 text-sm leading-6 text-indigo-950">
        FACT_FROM_JD means only that the quote appears literally in the pasted description. It does not mean the employer requires it or that a candidate meets it. Read negation and qualifiers in full. Grouping and normalized names are interpretations, not facts from the JD.
      </div>
      {analysis.truncated && <p role="status" className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-900">The extraction reached its item limit. These quotes are not a complete inventory; review the original JD below.</p>}
      <h3 className="mt-6 text-lg font-semibold">Extracted quotes ({analysis.requirement_count})</h3>
      {analysis.requirements.length === 0 ? (
        <p className="mt-3 text-sm text-slate-600">No supported requirement patterns were extracted. The original description is saved below; this does not mean it contains no requirements.</p>
      ) : (
        <ol className="mt-4 space-y-4">
          {[...analysis.requirements].sort((a, b) => a.position - b.position).map((requirement) => (
            <li key={requirement.id} className="rounded-2xl border border-slate-200 p-4">
              <p className="text-xs font-semibold text-indigo-700">{requirement.evidence_type} · Verbatim quote</p>
              <blockquote className="mt-3 whitespace-pre-wrap break-words border-l-2 border-indigo-200 pl-4 text-sm leading-7">{requirement.quote}</blockquote>
              <p className="mt-3 text-xs text-slate-500">Source characters {requirement.source_start}–{requirement.source_end} (zero-based Unicode code points, end exclusive)</p>
              <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                <p>Inferred group: <span className="font-medium">{requirement.group}</span> (interpretation)</p>
                {requirement.normalized_name && <p className="mt-1">Normalized name: <span className="font-medium">{requirement.normalized_name}</span> · {requirement.interpretation_type ?? "Interpretation"}</p>}
              </div>
            </li>
          ))}
        </ol>
      )}
      <details className="mt-6 rounded-2xl border border-slate-200 p-4">
        <summary className="cursor-pointer font-semibold">Original pasted job description</summary>
        <pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm leading-7 text-slate-700">{analysis.source_text}</pre>
      </details>
    </section>
  );
}

export default function JobMatchPage() {
  const [authRequired, setAuthRequired] = useState(false);
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [offset, setOffset] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const [history, setHistory] = useState<JDAnalysisList | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [analysis, setAnalysis] = useState<JDAnalysis | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const historyRequest = useRef<AbortController | null>(null);
  const detailRequest = useRef<AbortController | null>(null);
  const submitRequest = useRef<AbortController | null>(null);

  const requireSignIn = useCallback(() => {
    historyRequest.current?.abort();
    detailRequest.current?.abort();
    submitRequest.current?.abort();
    setAuthRequired(true);
    setHistory(null);
    setAnalysis(null);
  }, []);

  const handleAuthError = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.status === 401) {
      requireSignIn();
      return true;
    }
    return false;
  }, [requireSignIn]);

  useEffect(() => {
    const controller = new AbortController();
    historyRequest.current = controller;
    async function load() {
      const token = sessionStorage.getItem(TOKEN_KEY);
      if (!token) { requireSignIn(); return; }
      try {
        const result = await listJDAnalyses(token, PAGE_SIZE, offset, controller.signal);
        if (!controller.signal.aborted) { setHistory(result); setHistoryError(""); }
      } catch (error) {
        if (!controller.signal.aborted && !handleAuthError(error)) setHistoryError(errorMessage(error));
      } finally {
        if (!controller.signal.aborted) setHistoryLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [offset, refresh, handleAuthError, requireSignIn]);

  useEffect(() => () => {
    detailRequest.current?.abort();
    submitRequest.current?.abort();
  }, []);

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("analysis");
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (!id || !token) return;
    const controller = new AbortController();
    detailRequest.current = controller;
    getJDAnalysis(token, id, controller.signal).then((result) => {
      if (!controller.signal.aborted) { setAnalysis(result); setSelectedId(id); }
    }).catch((error: unknown) => {
      if (!controller.signal.aborted && !handleAuthError(error)) { setSelectedId(id); setDetailError(errorMessage(error)); }
    });
    return () => controller.abort();
  }, [handleAuthError]);

  function reloadHistory(nextOffset = offset) {
    historyRequest.current?.abort();
    setHistoryLoading(true);
    setHistoryError("");
    setOffset(nextOffset);
    setRefresh((value) => value + 1);
  }

  async function openAnalysis(id: string) {
    detailRequest.current?.abort();
    const controller = new AbortController();
    detailRequest.current = controller;
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (!token) { requireSignIn(); return; }
    setSelectedId(id);
    setAnalysis(null);
    setDetailError("");
    setDetailLoading(true);
    try {
      const result = await getJDAnalysis(token, id, controller.signal);
      if (!controller.signal.aborted) setAnalysis(result);
    } catch (error) {
      if (!controller.signal.aborted && !handleAuthError(error)) setDetailError(errorMessage(error));
    } finally {
      if (!controller.signal.aborted) setDetailLoading(false);
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitRequest.current && !submitRequest.current.signal.aborted) return;
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (!token) { requireSignIn(); return; }
    if (!title.trim() || !sourceText.trim() || Array.from(sourceText).length > 30000 || sourceText.includes("\0")) {
      setSubmitError("Enter a title and a nonblank description of at most 30,000 characters, without null characters.");
      return;
    }
    if (sourceUrl.trim()) {
      try {
        const url = new URL(sourceUrl.trim());
        if (!["http:", "https:"].includes(url.protocol)) throw new Error();
      } catch {
        setSubmitError("Use a valid HTTP or HTTPS source URL, or leave it blank.");
        return;
      }
    }
    detailRequest.current?.abort();
    setDetailLoading(false);
    setDetailError("");
    setAnalysis(null);
    setSelectedId(null);
    setSubmitting(true);
    setSubmitError("");
    const controller = new AbortController();
    submitRequest.current = controller;
    try {
      const result = await createJDAnalysis(token, {
        title: title.trim(), company: company.trim() || null,
        source_url: sourceUrl.trim() || null, source_text: sourceText,
      }, controller.signal);
      if (!controller.signal.aborted) {
        setAnalysis(result);
        setSelectedId(result.id);
        reloadHistory(0);
      }
    } catch (error) {
      if (!controller.signal.aborted && !handleAuthError(error)) {
        setSubmitError(`${errorMessage(error)} Your text is still here. If the connection failed, refresh history before resubmitting: the analysis may already have been saved.`);
      }
    } finally {
      if (!controller.signal.aborted) setSubmitting(false);
      if (submitRequest.current === controller) submitRequest.current = null;
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <p className="text-lg font-bold">CareerPilot AI</p>
          <Link href="/dashboard" className={buttonClass}>Dashboard</Link>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-6 py-10">
        <p className="text-sm font-semibold uppercase tracking-widest text-indigo-700">JD extraction & evidence comparison</p>
        <h1 className="mt-3 text-3xl font-bold">Understand a job description</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">Paste a job description to save and inspect its extracted quotes. Then optionally compare the saved requirements with your latest Career Twin evidence. Extraction remains separate from personalized comparison; neither predicts hiring outcomes.</p>
        {authRequired ? (
          <section className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-6" role="alert">
            <h2 className="font-semibold">Sign in to access your saved descriptions</h2>
            <p className="mt-2 text-sm">Your session is missing or has expired.</p>
            <Link href="/login" className={`${buttonClass} mt-4 inline-block`}>Sign in</Link>
          </section>
        ) : (
          <>
            <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold">New extraction</h2>
                <form onSubmit={submit} className="mt-5">
                  <fieldset disabled={submitting} className="space-y-4 disabled:opacity-70">
                    <div><label htmlFor="job-title" className="text-sm font-medium">Job title *</label><input id="job-title" required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} className={inputClass} /></div>
                    <div><label htmlFor="job-company" className="text-sm font-medium">Company (optional)</label><input id="job-company" maxLength={200} value={company} onChange={(event) => setCompany(event.target.value)} className={inputClass} /></div>
                    <div><label htmlFor="job-url" className="text-sm font-medium">Source URL (optional)</label><input id="job-url" type="url" maxLength={2048} value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} aria-describedby="url-help" className={inputClass} /><p id="url-help" className="mt-2 text-xs text-slate-500">Reference metadata only. The URL is not fetched; paste the description below.</p></div>
                    <div><label htmlFor="job-text" className="text-sm font-medium">Original job description *</label><textarea id="job-text" required rows={12} value={sourceText} onChange={(event) => setSourceText(event.target.value)} aria-describedby="text-help" className={inputClass} /><p id="text-help" className="mt-2 text-xs text-slate-500">{Array.from(sourceText).length.toLocaleString()} / 30,000 characters. Original spacing and wording are preserved.</p></div>
                    <button type="submit" className="rounded-xl bg-indigo-700 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-600 disabled:opacity-50">{submitting ? "Extracting and saving…" : "Extract and save JD"}</button>
                  </fieldset>
                  {submitError && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-800">{submitError}</p>}
                  {submitting && <p role="status" className="mt-3 text-sm text-slate-600">Saving your description and extracting quotes…</p>}
                </form>
              </section>
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" aria-labelledby="history-title" aria-busy={historyLoading}>
                <div className="flex flex-wrap items-center justify-between gap-3"><h2 id="history-title" className="text-xl font-semibold">Saved history</h2><button type="button" disabled={historyLoading || submitting} onClick={() => reloadHistory()} className={buttonClass}>Refresh</button></div>
                {historyLoading ? <p role="status" className="mt-5 text-sm text-slate-600">Loading saved descriptions…</p> : historyError ? <div role="alert" className="mt-4 text-sm text-red-800"><p>{historyError}</p><button type="button" className={`${buttonClass} mt-3`} onClick={() => reloadHistory()}>Retry history</button></div> : history && (
                  <>
                    {history.items.length === 0 ? <p className="mt-5 text-sm text-slate-600">{offset === 0 ? "No saved descriptions yet. Paste your first JD to begin." : "No descriptions on this page. Return to the previous page or refresh."}</p> : <ul className="mt-4 space-y-3">{history.items.map((item) => <li key={item.id}><button type="button" disabled={submitting} aria-pressed={selectedId === item.id} onClick={() => void openAnalysis(item.id)} className="w-full rounded-xl border border-slate-200 p-4 text-left hover:bg-indigo-50 aria-pressed:border-indigo-500 disabled:opacity-50"><span className="block break-words text-sm font-semibold">{item.title}</span>{item.company && <span className="mt-1 block break-words text-xs text-slate-600">{item.company}</span>}<span className="mt-2 block text-xs text-slate-500">{new Date(item.created_at).toLocaleDateString()} · {item.requirement_count} quotes{item.truncated ? " · Limited extraction" : ""}</span></button></li>)}</ul>}
                    <p className="mt-4 text-xs text-slate-500">{history.total === 0 ? "0 saved descriptions" : `${history.items.length ? history.offset + 1 : 0}–${history.offset + history.items.length} of ${history.total}`}</p>
                    <div className="mt-3 flex gap-2"><button type="button" disabled={offset === 0 || submitting} className={buttonClass} onClick={() => reloadHistory(Math.max(0, offset - PAGE_SIZE))}>Previous</button><button type="button" disabled={history.offset + history.limit >= history.total || submitting} className={buttonClass} onClick={() => reloadHistory(offset + PAGE_SIZE)}>Next</button></div>
                  </>
                )}
              </section>
            </div>
            {detailLoading && <p role="status" className="mt-8 text-sm text-slate-600">Opening saved extraction…</p>}
            {detailError && <div role="alert" className="mt-8 rounded-xl bg-red-50 p-4 text-sm text-red-800"><p>{detailError}</p>{selectedId && <button type="button" className={`${buttonClass} mt-3`} onClick={() => void openAnalysis(selectedId)}>Retry opening</button>}</div>}
            {analysis && <AnalysisDetail analysis={analysis} />}
            {analysis && <MatchPanel key={analysis.id} analysisId={analysis.id} />}
          </>
        )}
      </div>
    </main>
  );
}
