"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError } from "@/lib/api/client";
import { askAssistant, getAssistantStatus, type AssistantResponse, type AssistantStatus, type AssistantTopic } from "@/lib/api/assistant";

const button = "rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-slate-50 disabled:opacity-50";
const field = "mt-2 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm focus:outline-2 focus:outline-indigo-600";
const starters = ["What should I work on next?", "Explain my current skill gaps.", "Which certification should I prioritize?", "How does my profile align with my latest job analysis?"];
const topics: [AssistantTopic, string][] = [["auto", "Choose from my question"], ["next_steps", "Next steps / roadmap"], ["skills", "Skills and evidence"], ["profile", "Profile and career goal"], ["assessments", "Assessments"], ["certifications", "Certification recommendations"], ["job_match", "Saved JD comparison"], ["applications", "Applications"], ["progress", "Recorded progress"]];

export default function AssistantPage() {
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const [auth, setAuth] = useState(false);
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("");
  const [topic, setTopic] = useState<AssistantTopic>("auto");
  const [jd, setJD] = useState("");
  const [application, setApplication] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<{ question: string; response: AssistantResponse }[]>([]);
  const request = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      const token = sessionStorage.getItem("careerpilot_access_token");
      if (!token) { setAuth(true); return; }
      try {
        const result = await getAssistantStatus(token, controller.signal);
        if (!controller.signal.aborted) {
          setStatus(result); setError("");
          if (revision === 0) { const params = new URLSearchParams(window.location.search); setJD(params.get("jd") ?? ""); setApplication(params.get("application") ?? ""); }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          if (error instanceof ApiError && error.status === 401) setAuth(true);
          else setError("Assistant configuration status could not be loaded. Try again.");
        }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [revision]);
  useEffect(() => () => request.current?.abort(), []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (request.current || !question.trim()) return;
    const token = sessionStorage.getItem("careerpilot_access_token");
    if (!token) { setAuth(true); setMessages([]); return; }
    const controller = new AbortController(); request.current = controller;
    setBusy(true); setError("");
    const submitted = question.trim();
    try {
      const response = await askAssistant(token, { message: submitted, topic, jd_analysis_id: jd.trim() || null, application_id: application.trim() || null, allow_provider_processing: consent }, controller.signal);
      if (!controller.signal.aborted) { setMessages((old) => [...old.slice(-9), { question: submitted, response }]); setQuestion(""); }
    } catch (error) {
      if (!controller.signal.aborted) {
        if (error instanceof ApiError && error.status === 401) { setAuth(true); setMessages([]); }
        else if (error instanceof ApiError && error.status === 404) setError("The referenced resource was not found in your account. Check the selected IDs.");
        else if (error instanceof ApiError && error.status === 422) setError("Check the question (maximum 2,000 characters) and optional resource UUIDs.");
        else setError("The assistant request could not be completed. Your question is retained; no answer was fabricated.");
      }
    } finally { if (!controller.signal.aborted) setBusy(false); request.current = null; }
  }

  return <main className="min-h-screen bg-slate-50 text-slate-950"><div className="mx-auto max-w-5xl px-6 py-10">
    <nav className="mb-6 flex gap-3"><Link href="/dashboard" className={button}>Dashboard</Link><Link href="/job-match" className={button}>Job Match</Link></nav>
    <h1 className="text-3xl font-bold">CareerPilot AI Assistant</h1><p className="mt-3 text-sm leading-6 text-slate-600">Guidance grounded in your recorded CareerPilot state. ACIF and structured services remain authoritative. This assistant does not change your evidence, applications, or roadmap.</p>
    {auth ? <p role="alert" className="mt-6"><Link href="/login" className={button}>Sign in to use the assistant</Link></p> : <>
      {loading && <p role="status" className="mt-6">Checking assistant availability…</p>}
      {status && <div className={`mt-6 rounded-xl p-4 text-sm ${status.provider_status === "READY" ? "bg-indigo-50" : "bg-amber-50"}`} role="status"><p className="font-semibold">{status.provider_status === "READY" ? "Structured grounding · optional provider configured" : "CareerPilot AI Assistant is not configured yet."}</p><p className="mt-2">{status.message}</p><p className="mt-2">Other CareerPilot features remain available. The provider selects relevant statements; unrestricted generated claims and semantic retrieval are not enabled.</p></div>}
      {error && <p role="alert" className="mt-4 text-sm text-red-800">{error}</p>}
      <button className={`${button} mt-4`} disabled={loading || busy} onClick={() => { setLoading(true); setRevision((value) => value + 1); }}>Refresh availability</button>
      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6" aria-labelledby="ask-title"><h2 id="ask-title" className="text-xl font-semibold">Ask about your recorded state</h2>
        <div className="mt-4 flex flex-wrap gap-2">{starters.map((text) => <button key={text} className={button} disabled={busy} onClick={() => { setQuestion(text); setTopic("auto"); }}>{text}</button>)}</div>
        <form onSubmit={submit}><fieldset disabled={busy || loading} className="mt-5 space-y-4">
          <label className="block text-sm font-medium">Question<textarea className={field} rows={4} required maxLength={2000} value={question} onChange={(event) => setQuestion(event.target.value)} /></label>
          <label className="block text-sm font-medium">Context topic<select className={field} value={topic} onChange={(event) => setTopic(event.target.value as AssistantTopic)}>{topics.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <details><summary className="cursor-pointer text-sm font-semibold">Optional owned resource references</summary><div className="mt-3 grid gap-4 sm:grid-cols-2"><label className="text-sm">JD analysis UUID<input className={field} maxLength={36} value={jd} onChange={(event) => setJD(event.target.value)} /></label><label className="text-sm">Application UUID<input className={field} maxLength={36} value={application} onChange={(event) => setApplication(event.target.value)} /></label></div></details>
          <label className="flex items-start gap-3 text-sm leading-6"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1" />I allow this question and limited relevant summaries to be sent to the configured provider. Do not put passwords or unnecessary personal information in your question.</label>
          <p className="text-xs leading-5 text-slate-500">Raw resume/JD text, application notes and profile contact details are excluded. Questions are independent; earlier messages are not automatically sent. This page retains at most ten responses until you leave or clear it.</p>
          <button type="submit" className={button} disabled={!consent || status?.provider_status !== "READY"}>{busy ? "Preparing grounded response…" : "Ask CareerPilot"}</button>
        </fieldset></form>
      </section>
      <section className="mt-8" aria-labelledby="responses-title" aria-busy={busy}><div className="flex justify-between gap-4"><h2 id="responses-title" className="text-xl font-semibold">Conversation</h2><button className={button} disabled={busy || messages.length === 0} onClick={() => setMessages([])}>Clear messages</button></div>
        {messages.length === 0 && <p className="mt-4 text-sm text-slate-600">No questions yet. Choose a starter prompt or ask a specific question. Missing information will remain unavailable.</p>}
        {busy && <p role="status" className="mt-4 text-sm">Retrieving bounded context and requesting source selection…</p>}
        <div className="mt-5 space-y-6">{messages.map((entry, index) => <article key={index} className="rounded-2xl border border-slate-200 bg-white p-5"><p className="whitespace-pre-wrap break-words font-semibold">You: {entry.question}</p><p className="mt-4 whitespace-pre-wrap break-words text-sm leading-7">{entry.response.answer ?? entry.response.message}</p>{entry.response.context_sources.length > 0 && <details className="mt-4"><summary className="cursor-pointer text-sm font-semibold">Grounding sources and provenance</summary><ul className="mt-3 space-y-3">{entry.response.context_sources.map((source) => <li key={source.id} className="text-sm"><Link href={source.href} className="text-indigo-700 underline">{source.kind.replaceAll("_", " ")}</Link><p className="mt-1 text-xs text-slate-500">{source.provenance}</p></li>)}</ul></details>}<p className="mt-4 text-xs text-slate-500">Provider-selected statements retain their original fact/model/recommendation classification; no new factual prose is accepted.</p><details className="mt-3"><summary className="cursor-pointer text-xs font-semibold">Limitations</summary><ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-500">{entry.response.limitations.map((text) => <li key={text}>{text}</li>)}</ul></details></article>)}</div>
      </section>
    </>}
  </div></main>;
}
