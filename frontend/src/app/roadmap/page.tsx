"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getRoadmap,
  RoadmapItem,
  RoadmapStatus,
  updateRoadmapItemStatus,
} from "@/lib/api/roadmap";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";

const STATUS_OPTIONS: RoadmapStatus[] = [
  "NOT_STARTED",
  "IN_PROGRESS",
  "COMPLETED",
  "SKIPPED",
];

function formatStatus(status: string) {
  return status
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function statusClasses(status: RoadmapStatus) {
  if (status === "COMPLETED") return "bg-emerald-50 text-emerald-700";
  if (status === "IN_PROGRESS") return "bg-blue-50 text-blue-700";
  if (status === "SKIPPED") return "bg-slate-100 text-slate-600";
  return "bg-amber-50 text-amber-700";
}

function RoadmapCard({
  item,
  updatingId,
  onStatusChange,
}: {
  item: RoadmapItem;
  updatingId: string | null;
  onStatusChange: (item: RoadmapItem, status: RoadmapStatus) => void;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">
            {item.order}
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {item.provenance.replaceAll("_", " ")}
            </p>
            <h2 className="mt-1 text-xl font-bold text-slate-950">
              {item.item_key.split(":").slice(1).join(":") || "Development action"}
            </h2>
          </div>
        </div>

        <select
          aria-label={`Status for roadmap item ${item.order}`}
          value={item.status}
          disabled={updatingId === item.id}
          onChange={(event) =>
            onStatusChange(item, event.target.value as RoadmapStatus)
          }
          className={`rounded-full border-0 px-3 py-2 text-xs font-semibold outline-none ${statusClasses(item.status)}`}
        >
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {formatStatus(status)}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Current evidence state
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {item.current_evidence_state}
          </p>
        </div>
        <div className="rounded-xl bg-blue-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
            Why this is recommended
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{item.reason}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Recommended action
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {item.recommended_action}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Evidence-building milestone
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {item.evidence_building_action} {item.milestone}
          </p>
        </div>
      </div>

      <p className="mt-5 text-xs text-slate-400">
        ACIF {item.model_version} · Career Twin snapshot v{item.snapshot_version}
      </p>
    </article>
  );
}

export default function RoadmapPage() {
  const router = useRouter();
  const [roadmap, setRoadmap] = useState<Awaited<ReturnType<typeof getRoadmap>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadRoadmap() {
      const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
      if (!accessToken) {
        router.replace("/login");
        return;
      }

      try {
        const response = await getRoadmap(accessToken);
        if (!cancelled) setRoadmap(response);
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Your learning roadmap could not be loaded.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadRoadmap();
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function handleStatusChange(item: RoadmapItem, status: RoadmapStatus) {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
    if (!accessToken || !roadmap) {
      router.replace("/login");
      return;
    }

    try {
      setUpdatingId(item.id);
      setError(null);
      const updated = await updateRoadmapItemStatus(accessToken, item.id, status);
      setRoadmap({
        ...roadmap,
        items: roadmap.items.map((current) =>
          current.id === updated.id ? updated : current,
        ),
      });
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "The roadmap status could not be updated.",
      );
    } finally {
      setUpdatingId(null);
    }
  }

  if (loading) {
    return <main className="min-h-screen bg-slate-50 px-6 py-16"><div className="mx-auto max-w-5xl text-sm text-slate-500">Loading your evidence-grounded roadmap…</div></main>;
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">CareerPilot AI</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Personalized Learning Roadmap</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              A deterministic development plan derived from your target career, Career Twin, evidence gaps, and ACIF actions. It is not generic advice and it does not represent employment probability.
            </p>
          </div>
          <button type="button" onClick={() => router.push("/dashboard")} className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700">Dashboard</button>
        </div>

        {error && <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

        {!roadmap ? (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <h2 className="font-semibold text-slate-900">Roadmap unavailable</h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">Complete your career goal and create enough Career Twin evidence for ACIF to generate a roadmap.</p>
          </section>
        ) : (
          <>
            <section className="mt-8 rounded-2xl bg-slate-950 p-6 text-white">
              <p className="text-xs font-semibold uppercase tracking-wide text-blue-300">Target role</p>
              <h2 className="mt-2 text-2xl font-bold">{roadmap.target_role}</h2>
              <p className="mt-2 text-sm text-slate-300">Items are recalculated from the current Career Twin snapshot. What-If simulation state is not persisted into this roadmap.</p>
            </section>

            {roadmap.items.length === 0 ? (
              <section className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
                <h2 className="font-semibold text-emerald-900">No prioritized actions currently available</h2>
                <p className="mt-2 text-sm leading-6 text-emerald-800">ACIF did not return a current minimum-action item. Continue adding real evidence or assessments as your Career Twin evolves.</p>
              </section>
            ) : (
              <section className="mt-8 space-y-5">
                {roadmap.items.map((item) => <RoadmapCard key={item.id} item={item} updatingId={updatingId} onStatusChange={handleStatusChange} />)}
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}
