"use client";

import { useMemo, useState } from "react";

import {
  simulateCareerSkillEvidence,
  type CareerSimulationResponse,
  type TechnologyEvidenceItem,
} from "@/lib/api/acif";

interface WhatIfSimulatorProps {
  careerId: string;
  technologies: TechnologyEvidenceItem[];
}

type ScenarioValue = "0.50" | "0.75" | "0.90";

const scenarios: {
  value: ScenarioValue;
  label: string;
  description: string;
}[] = [
  {
    value: "0.50",
    label: "Moderate supporting evidence",
    description:
      "Explore a hypothetical state with moderate evidence confidence.",
  },
  {
    value: "0.75",
    label: "Strong supporting evidence",
    description:
      "Explore a hypothetical state with strong evidence confidence.",
  },
  {
    value: "0.90",
    label: "Very strong supporting evidence",
    description:
      "Explore a hypothetical state with very strong evidence confidence.",
  },
];

function percent(value: number | null) {
  if (value === null) {
    return "Not available";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function signedPercent(value: number | null) {
  if (value === null) {
    return "Not available";
  }

  const percentage = value * 100;

  if (percentage > 0) {
    return `+${percentage.toFixed(1)}%`;
  }

  return `${percentage.toFixed(1)}%`;
}

function MetricChange({
  title,
  before,
  after,
  delta,
}: {
  title: string;
  before: number | null;
  after: number | null;
  delta: number | null;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <p className="text-sm font-semibold text-slate-900">
        {title}
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Before
          </p>

          <p className="mt-2 text-xl font-bold text-slate-950">
            {percent(before)}
          </p>
        </div>

        <div className="rounded-xl bg-blue-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-blue-600">
            Simulated
          </p>

          <p className="mt-2 text-xl font-bold text-blue-700">
            {percent(after)}
          </p>
        </div>
      </div>

      <p className="mt-4 text-sm font-semibold text-emerald-700">
        Change: {signedPercent(delta)}
      </p>
    </div>
  );
}

export default function WhatIfSimulator({
  careerId,
  technologies,
}: WhatIfSimulatorProps) {
  const availableTechnologies = useMemo(() => {
    return [...technologies].sort((a, b) =>
      a.technology.localeCompare(b.technology)
    );
  }, [technologies]);

  const [skillName, setSkillName] = useState(
    availableTechnologies[0]?.technology ?? ""
  );

  const [scenario, setScenario] =
    useState<ScenarioValue>("0.75");

  const [result, setResult] =
    useState<CareerSimulationResponse | null>(null);

  const [isSimulating, setIsSimulating] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  async function runSimulation() {
    if (!skillName) {
      setError("Select a technology to simulate.");
      return;
    }

    const accessToken = sessionStorage.getItem(
      "careerpilot_access_token"
    );

    if (!accessToken) {
      setError(
        "Your session is unavailable. Sign in again and retry."
      );
      return;
    }

    setIsSimulating(true);
    setError(null);
    setResult(null);

    try {
      const response =
        await simulateCareerSkillEvidence(
          accessToken,
          careerId,
          {
            simulation_type:
              "ADD_SKILL_EVIDENCE",
            skill_name: skillName,
            simulated_confidence:
              Number(scenario),
          }
        );

      setResult(response);
    } catch (err) {
      console.error(
        "Career simulation failed:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to run the simulation."
      );
    } finally {
      setIsSimulating(false);
    }
  }

  const selectedScenario =
    scenarios.find(
      (item) => item.value === scenario
    ) ?? scenarios[1];

  return (
    <section className="mt-10 overflow-hidden rounded-3xl border border-blue-200 bg-white shadow-sm">
      <div className="border-b border-blue-100 bg-blue-50/70 p-6 sm:p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">
              ACIF What-If Simulator
            </p>

            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
              Explore a hypothetical evidence change
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              Explore how the current ACIF model
              state would change if stronger
              supporting evidence were available for
              a technology.
            </p>
          </div>

          <div className="w-fit rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-700">
            Career Twin remains unchanged
          </div>
        </div>
      </div>

      <div className="p-6 sm:p-7">
        <div className="grid gap-5 lg:grid-cols-2">
          <div>
            <label
              htmlFor="simulation-technology"
              className="text-sm font-semibold text-slate-900"
            >
              Technology
            </label>

            <select
              id="simulation-technology"
              value={skillName}
              onChange={(event) => {
                setSkillName(
                  event.target.value
                );
                setResult(null);
                setError(null);
              }}
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              {availableTechnologies.map(
                (technology) => (
                  <option
                    key={
                      technology.normalized_technology
                    }
                    value={
                      technology.technology
                    }
                  >
                    {technology.technology}
                  </option>
                )
              )}
            </select>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              These technologies come from the
              selected occupation&apos;s current
              market-signal set.
            </p>
          </div>

          <div>
            <label
              htmlFor="simulation-scenario"
              className="text-sm font-semibold text-slate-900"
            >
              Evidence scenario
            </label>

            <select
              id="simulation-scenario"
              value={scenario}
              onChange={(event) => {
                setScenario(
                  event.target
                    .value as ScenarioValue
                );
                setResult(null);
                setError(null);
              }}
              className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            >
              {scenarios.map((item) => (
                <option
                  key={item.value}
                  value={item.value}
                >
                  {item.label}
                </option>
              ))}
            </select>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              {selectedScenario.description}
              {" "}
              This is an ACIF simulation
              parameter, not a proficiency score.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={runSimulation}
          disabled={
            isSimulating || !skillName
          }
          className="mt-6 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSimulating
            ? "Running simulation..."
            : "Run What-If Simulation"}
        </button>

        {error && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4">
            <p className="text-sm font-medium text-red-700">
              {error}
            </p>
          </div>
        )}

        {result && (
          <div className="mt-8">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Simulation result
                </p>

                <h3 className="mt-1 text-xl font-bold text-slate-950">
                  {result.simulation.skill_name}
                </h3>
              </div>

              <span className="w-fit rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                {result.database_mutated
                  ? "Database changed"
                  : "No data saved"}
              </span>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              <MetricChange
                title="Technology Evidence Coverage"
                before={
                  result.delta
                    .readiness_changes
                    .technology_evidence_coverage
                    .before
                }
                after={
                  result.delta
                    .readiness_changes
                    .technology_evidence_coverage
                    .after
                }
                delta={
                  result.delta
                    .readiness_changes
                    .technology_evidence_coverage
                    .delta
                }
              />

              <MetricChange
                title="Technology Evidence Strength"
                before={
                  result.delta
                    .readiness_changes
                    .technology_evidence_strength
                    .before
                }
                after={
                  result.delta
                    .readiness_changes
                    .technology_evidence_strength
                    .after
                }
                delta={
                  result.delta
                    .readiness_changes
                    .technology_evidence_strength
                    .delta
                }
              />
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-emerald-50 p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                  Strong evidence
                </p>

                <p className="mt-2 text-2xl font-bold text-emerald-800">
                  {
                    result.delta
                      .technology_gap_changes
                      .strong_evidence_count
                      .before
                  }
                  {" → "}
                  {
                    result.delta
                      .technology_gap_changes
                      .strong_evidence_count
                      .after
                  }
                </p>
              </div>

              <div className="rounded-2xl bg-amber-50 p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-amber-700">
                  Needs strengthening
                </p>

                <p className="mt-2 text-2xl font-bold text-amber-800">
                  {
                    result.delta
                      .technology_gap_changes
                      .evidence_needs_strengthening_count
                      .before
                  }
                  {" → "}
                  {
                    result.delta
                      .technology_gap_changes
                      .evidence_needs_strengthening_count
                      .after
                  }
                </p>
              </div>

              <div className="rounded-2xl bg-slate-100 p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Missing evidence
                </p>

                <p className="mt-2 text-2xl font-bold text-slate-800">
                  {
                    result.delta
                      .technology_gap_changes
                      .missing_evidence_count
                      .before
                  }
                  {" → "}
                  {
                    result.delta
                      .technology_gap_changes
                      .missing_evidence_count
                      .after
                  }
                </p>
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-sm font-semibold text-slate-900">
                What this result means
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                {result.delta.interpretation}
              </p>

              <p className="mt-3 text-xs leading-5 text-slate-500">
                This simulation changes an ACIF
                model state only. It is not a causal
                estimate of hiring, placement,
                employability, or career success.
              </p>
            </div>

            {!result.database_mutated && (
              <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                <p className="text-sm font-semibold text-emerald-800">
                  Your Career Twin was not modified
                </p>

                <p className="mt-1 text-sm leading-6 text-emerald-700">
                  The before/after values exist only
                  for this hypothetical simulation.
                  Your saved evidence remains exactly
                  as it was before running it.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}