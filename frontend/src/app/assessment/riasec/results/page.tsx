"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getLatestRiasecAssessment,
  getRiasecMatches,
  type CareerInterestMatch,
  type RiasecAssessmentResult,
  type RiasecScores,
} from "@/lib/api/psychometrics";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";

const DIMENSIONS: {
  key: keyof RiasecScores;
  code: string;
  name: string;
  description: string;
}[] = [
  {
    key: "realistic",
    code: "R",
    name: "Realistic",
    description: "Practical, hands-on and technical activities",
  },
  {
    key: "investigative",
    code: "I",
    name: "Investigative",
    description: "Analysis, research and problem solving",
  },
  {
    key: "artistic",
    code: "A",
    name: "Artistic",
    description: "Creativity, expression and original ideas",
  },
  {
    key: "social",
    code: "S",
    name: "Social",
    description: "Helping, teaching and working with people",
  },
  {
    key: "enterprising",
    code: "E",
    name: "Enterprising",
    description: "Leadership, persuasion and initiative",
  },
  {
    key: "conventional",
    code: "C",
    name: "Conventional",
    description: "Organization, structure and detail",
  },
];

function scorePercent(value: number) {
  return Math.round(value * 100);
}

export default function RiasecResultsPage() {
  const router = useRouter();

  const [assessment, setAssessment] =
    useState<RiasecAssessmentResult | null>(null);

  const [matches, setMatches] = useState<
    CareerInterestMatch[]
  >([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(
    null
  );

  useEffect(() => {
    async function loadResults() {
      const accessToken = sessionStorage.getItem(
        ACCESS_TOKEN_KEY
      );

      if (!accessToken) {
        router.replace("/login");
        return;
      }

      try {
        const [latestAssessment, careerMatches] =
          await Promise.all([
            getLatestRiasecAssessment(accessToken),
            getRiasecMatches(accessToken, 10),
          ]);

        setAssessment(latestAssessment);
        setMatches(careerMatches);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load your assessment results."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadResults();
  }, [router]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

          <p className="mt-4 text-sm text-slate-600">
            Building your career-interest profile...
          </p>
        </div>
      </main>
    );
  }

  if (error || !assessment) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-slate-950">
            Results unavailable
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            {error ??
              "We could not find a completed assessment."}
          </p>

          <button
            type="button"
            onClick={() =>
              router.push("/assessment/riasec")
            }
            className="mt-6 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Take Assessment
          </button>
        </div>
      </main>
    );
  }

  const scores = assessment.profile.scores;

  const sortedDimensions = [...DIMENSIONS].sort(
    (a, b) => scores[b.key] - scores[a.key]
  );

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 lg:py-16">
        <header className="mb-10">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="mb-6 text-sm font-medium text-slate-500 transition hover:text-slate-950"
          >
            ← Back to dashboard
          </button>

          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            CareerPilot AI
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Your Career Interest Profile
          </h1>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Your responses were analyzed across the six
            RIASEC career-interest dimensions. CareerPilot
            then compared the shape of your profile with
            occupational interest profiles in our O*NET
            career knowledge base.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[300px_1fr]">
          <div className="rounded-3xl bg-slate-950 p-8 text-white shadow-sm">
            <p className="text-sm font-medium text-slate-300">
              Your dominant interest code
            </p>

            <div className="mt-5 text-6xl font-bold tracking-wider">
              {assessment.profile.dominant_code}
            </div>

            <p className="mt-5 text-sm leading-6 text-slate-300">
              The code represents your three strongest
              interest dimensions from this assessment.
            </p>

            <button
              type="button"
              onClick={() =>
                router.push("/assessment/riasec")
              }
              className="mt-8 rounded-lg border border-slate-700 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              Retake Assessment
            </button>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <h2 className="text-xl font-semibold text-slate-950">
              Interest Dimensions
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Higher values indicate stronger expressed
              interest in that type of activity.
            </p>

            <div className="mt-7 space-y-6">
              {sortedDimensions.map((dimension) => {
                const percentage = scorePercent(
                  scores[dimension.key]
                );

                return (
                  <div key={dimension.key}>
                    <div className="mb-2 flex items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-xs font-bold text-blue-700">
                            {dimension.code}
                          </span>

                          <span className="font-medium text-slate-900">
                            {dimension.name}
                          </span>
                        </div>

                        <p className="mt-1 text-xs text-slate-500">
                          {dimension.description}
                        </p>
                      </div>

                      <span className="text-sm font-semibold text-slate-900">
                        {percentage}%
                      </span>
                    </div>

                    <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-blue-600"
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="mt-10">
          <div className="mb-6">
            <h2 className="text-2xl font-bold tracking-tight text-slate-950">
              Interest-Aligned Careers
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              These occupations have interest profiles
              similar to yours. Interest alignment is one
              signal only; later CareerPilot will combine
              this with verified skills, projects,
              assessments and career goals.
            </p>
          </div>

          {matches.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
              <p className="text-sm text-slate-600">
                No career matches are currently available.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {matches.map((career, index) => (
                <article
                  key={career.career_id}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300 hover:shadow-md"
                >
                  <div className="flex items-start justify-between gap-5">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
                        Match {index + 1}
                      </p>

                      <h3 className="mt-2 text-lg font-semibold text-slate-950">
                        {career.title}
                      </h3>

                      <p className="mt-1 text-xs text-slate-500">
                        O*NET {career.onet_soc_code}
                        {career.job_zone !== null
                          ? ` • Job Zone ${career.job_zone}`
                          : ""}
                      </p>
                    </div>

                    <div className="shrink-0 rounded-xl bg-blue-50 px-3 py-2 text-center">
                      <div className="text-lg font-bold text-blue-700">
                        {Math.round(
                          career.interest_alignment_percent
                        )}
                        %
                      </div>

                      <div className="text-[10px] font-medium uppercase tracking-wide text-blue-600">
                        Alignment
                      </div>
                    </div>
                  </div>

                  {career.description && (
                    <p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-600">
                      {career.description}
                    </p>
                  )}

                  <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                    <span className="text-xs text-slate-500">
                      Career interest code
                    </span>

                    <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                      {career.dominant_code}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="mt-10 rounded-2xl border border-blue-100 bg-blue-50 p-6">
          <h2 className="font-semibold text-slate-950">
            How should I interpret these results?
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            Interest alignment describes similarity between
            your expressed interests and an occupation&apos;s
            RIASEC profile. It is not a prediction of hiring,
            salary, placement or career success.
          </p>
        </section>
      </div>
    </main>
  );
}